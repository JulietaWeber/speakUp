import hashlib
import json
import os
import re
import threading

import numpy as np

from morfologia import quitar_tildes

INICIO = "<s>"               # inicio de frase: se agrega si hay menos de 3 palabras
MAX_CONTEXTO = 3
TOP_K = 3
SIMILITUD_MINIMA = 0.55      # coseno mínimo para reemplazar una palabra desconocida
BETA_USUARIO = 2.0           # peso usuario = c / (c + BETA): con 2 usos del contexto, 50%

_PALABRA = re.compile(r"[a-záéíóúüñ]+")


def tokenizar(texto):
    """'¿Quiero IR al parque?' -> ['quiero', 'ir', 'al', 'parque']."""
    return _PALABRA.findall(texto.lower())


def normalizar_palabras(palabras):
    """Lista de strings del back (pueden traer mayúsculas, puntuación o más
    de una palabra, ej. "por favor") -> lista plana de tokens."""
    tokens = []
    for p in palabras:
        if isinstance(p, str):
            tokens.extend(tokenizar(p))
    return tokens


def _id_seguro(user_id):
    """Nombre de archivo seguro para un user_id arbitrario (evita '../')."""
    limpio = re.sub(r"[^A-Za-z0-9_-]", "_", str(user_id))[:60] or "_"
    if limpio != str(user_id):
        limpio += "_" + hashlib.sha1(str(user_id).encode("utf-8")).hexdigest()[:10]
    return limpio


# /predecir: n-gramas Kneser-Ney de scripts/entrenar_prediccion.py, mezclados
# con el historial del usuario. /reentrenar: suma frases a ese historial.
class Predictor:
    def __init__(self, ruta_base, dir_usuarios, vector_de=None):
        """`ruta_base`: ruta sin extensión de modelo_prediccion.{npz,json}.
        `vector_de(palabra)`: vector de spaCy de una palabra o None."""
        with open(ruta_base + ".json", encoding="utf-8") as f:
            meta = json.load(f)
        datos = np.load(ruta_base + ".npz")
        self.vocab = meta["vocab"]
        self.idx = {w: i for i, w in enumerate(self.vocab)}
        self.fila = {c: i for i, c in enumerate(meta["contextos"])}
        self.unigrama = datos["unigrama"].astype(np.float64)
        self.gamma = datos["gamma"].astype(np.float64)
        self.indptr = datos["indptr"]
        self.indices = datos["indices"]
        self.valores = datos["valores"].astype(np.float64)
        self.excluir = np.zeros(len(self.vocab), dtype=bool)
        self.dir_usuarios = dir_usuarios
        self._lock = threading.Lock()
        self._cache_usuarios = {}

        # Sin tildes -> palabra del vocabulario más frecuente con esa forma.
        self.sin_tildes = {}
        for w in sorted(self.vocab, key=lambda w: -self.unigrama[self.idx[w]]):
            self.sin_tildes.setdefault(quitar_tildes(w), w)

        # Matriz de vectores normalizados del vocabulario, para palabras nuevas.
        self.vector_de = vector_de
        self.vecinos_vocab, self.matriz = [], None
        if vector_de is not None:
            filas = []
            for w in self.vocab:
                v = vector_de(w)
                if v is not None and np.any(v):
                    self.vecinos_vocab.append(w)
                    filas.append(v / (np.linalg.norm(v) + 1e-8))
            if filas:
                self.matriz = np.stack(filas).astype(np.float32)
        self._cache_mapeo = {}

    # ── Contexto ──────────────────────────────────────────────────────────────

    def _mapear(self, palabra, vocab_usuario=()):
        """Palabra del vocabulario equivalente a `palabra`, o None."""
        # una palabra desconocida se cambia por la misma sin tildes ("mama" ->
        # "mamá") o por la más parecida según los vectores de spaCy
        if palabra in self.idx or palabra in vocab_usuario:
            return palabra
        if palabra in self._cache_mapeo:
            return self._cache_mapeo[palabra]
        res = self.sin_tildes.get(quitar_tildes(palabra))
        if res is None and self.matriz is not None:
            v = self.vector_de(palabra)
            if v is not None and np.any(v):
                sims = self.matriz @ (v / (np.linalg.norm(v) + 1e-8))
                mejor = int(np.argmax(sims))
                if sims[mejor] >= SIMILITUD_MINIMA:
                    res = self.vecinos_vocab[mejor]
        if len(self._cache_mapeo) < 50000:
            self._cache_mapeo[palabra] = res
        return res

    def contexto(self, palabras, vocab_usuario=()):
        """Tokens de contexto listos para el modelo: últimas 3 palabras
        (mapeadas al vocabulario) y <s> al principio si la frase tiene menos
        de 3 palabras (el back manda todas las que hay si son menos de 3)."""
        tokens = normalizar_palabras(palabras)
        inicio = len(tokens) < MAX_CONTEXTO
        tokens = tokens[-MAX_CONTEXTO:]
        ctx = [INICIO] if inicio else []
        for t in tokens:
            m = self._mapear(t, vocab_usuario)
            if m is None:
                ctx = []          # palabra irreconocible: se usa lo que viene después
            else:
                ctx.append(m)
        return ctx[-MAX_CONTEXTO:]

    # ── Distribuciones ────────────────────────────────────────────────────────

    def distribucion_base(self, ctx):
        # interpolación KN: del unigrama a cada contexto más largo conocido
        # (cuentas de arrays numpy, menos de 1 ms)
        p = self.unigrama.copy()
        for k in range(1, len(ctx) + 1):
            fila = self.fila.get(" ".join(ctx[-k:]))
            if fila is None:
                continue
            a, b = self.indptr[fila], self.indptr[fila + 1]
            p *= self.gamma[fila]
            p[self.indices[a:b]] += self.valores[a:b]
        return p

    def predecir(self, user_id, palabras, k=TOP_K):
        usuario = self.datos_usuario(user_id)
        vocab_usuario = usuario["vocab"]
        ctx = self.contexto(palabras, vocab_usuario)
        ctx_base = [w if w in self.idx or w == INICIO else None for w in ctx]
        # palabras que solo conoce el usuario: el modelo base no las usa
        while None in ctx_base:
            ctx_base = ctx_base[ctx_base.index(None) + 1:]
        p = self.distribucion_base(ctx_base)

        # mezcla con el usuario: más peso cuantas más veces usó este contexto
        extra = {}
        cuentas, total = self._cuentas_usuario(usuario, ctx)
        if total:
            lam = total / (total + BETA_USUARIO)
            p *= (1 - lam)
            for w, c in cuentas.items():
                if w in self.idx:
                    p[self.idx[w]] += lam * c / total
                else:
                    extra[w] = lam * c / total

        ultima = normalizar_palabras(palabras)[-1:]
        candidatos = np.argpartition(-p, k + 1)[: k + 1]
        lista = [(self.vocab[i], float(p[i])) for i in candidatos]
        lista += list(extra.items())
        lista = [(w, pr) for w, pr in lista if w not in ultima]
        lista.sort(key=lambda x: -x[1])
        lista = lista[:k]
        if len(lista) < k:  # nunca debería pasar, pero siempre se devuelven k
            for i in np.argsort(-p):
                w = self.vocab[int(i)]
                if all(w != x for x, _ in lista):
                    lista.append((w, float(p[int(i)])))
                if len(lista) == k:
                    break
        return [{"palabra": w, "probabilidad": round(pr * 100, 2)} for w, pr in lista]

    # ── Usuarios ──────────────────────────────────────────────────────────────
    # Historial en modelos_usuarios/<id>.json: cuántas veces usó cada palabra
    # después de cada contexto (acumulativo).

    def _ruta_usuario(self, user_id):
        return os.path.join(self.dir_usuarios, _id_seguro(user_id) + ".json")

    def datos_usuario(self, user_id):
        ruta = self._ruta_usuario(user_id)
        try:
            mtime = os.path.getmtime(ruta)
        except OSError:
            return {"contextos": {}, "vocab": set()}
        cache = self._cache_usuarios.get(ruta)
        if cache and cache[0] == mtime:
            return cache[1]
        with open(ruta, encoding="utf-8") as f:
            crudo = json.load(f)
        datos = {"contextos": crudo.get("contextos", {})}
        datos["vocab"] = {w for cuentas in datos["contextos"].values() for w in cuentas}
        self._cache_usuarios[ruta] = (mtime, datos)
        return datos

    @staticmethod
    def _cuentas_usuario(usuario, ctx):
        """Cuentas del usuario para el contexto más largo que haya usado."""
        for k in range(len(ctx), 0, -1):
            cuentas = usuario["contextos"].get(" ".join(ctx[-k:]))
            if cuentas:
                return cuentas, sum(cuentas.values())
        return {}, 0

    def reentrenar(self, user_id, datos):
        """Suma al historial del usuario los pares (contexto -> palabra
        siguiente) de cada frase. Es acumulativo y tarda milisegundos."""
        frases = []
        for registro in datos or []:
            frase = registro.get("frase") if isinstance(registro, dict) else registro
            if isinstance(frase, str):
                frase = [frase]
            if isinstance(frase, list):
                tokens = normalizar_palabras(frase)
                if tokens:
                    frases.append(tokens)
        if not frases:
            return {"status": "sin_datos"}

        with self._lock:
            ruta = self._ruta_usuario(user_id)
            contextos = {}
            if os.path.exists(ruta):
                with open(ruta, encoding="utf-8") as f:
                    contextos = json.load(f).get("contextos", {})
            pares = 0
            for tokens in frases:
                seq = [INICIO] + tokens
                for i in range(1, len(seq)):
                    siguiente = seq[i]
                    for k in range(1, MAX_CONTEXTO + 1):
                        if i - k < 0:
                            break
                        clave = " ".join(seq[i - k:i])
                        cuentas = contextos.setdefault(clave, {})
                        cuentas[siguiente] = cuentas.get(siguiente, 0) + 1
                    pares += 1
            os.makedirs(self.dir_usuarios, exist_ok=True)
            tmp = ruta + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"user_id": str(user_id), "contextos": contextos}, f, ensure_ascii=False)
            os.replace(tmp, ruta)
            self._cache_usuarios.pop(ruta, None)
        return {"status": "ok", "pares_entrenados": pares}
