"""
Entrena un modelo de corrección de frases para CAA: recibe palabras sueltas
seleccionadas por el usuario (en cualquier orden) y aprende a producir la
frase natural en español correspondiente, usando EXACTAMENTE esas palabras
(reordenadas y conjugadas) más el glue gramatical mínimo (artículos,
preposiciones, pronombres, etc. - ver gramatica.py).

Arquitectura: seq2seq encoder-decoder con atención (Bahdanau) sobre GRUs de
una sola capa y una sola dirección, liviano para que la inferencia sea
rápida en el servidor:
- Encoder: cada palabra de entrada se representa con su vector de spaCy
  (embeddings preentrenados en español). Esto es clave para generalizar a
  frases nunca vistas: si el usuario elige un sinónimo o una palabra nueva,
  su vector va a estar cerca de palabras que el modelo sí vio entrenando.
- Decoder: GRU con atención que genera la frase palabra por palabra a partir
  de un vocabulario de salida aprendido del dataset.
- Restricción de vocabulario en inferencia: en cada paso de generación se
  enmascaran (logit = -inf) todos los tokens del vocabulario que no sean ni
  palabras funcionales cerradas ni derivados de alguna palabra de entrada.
  Así el modelo puede reordenar y conjugar, pero estructuralmente NO puede
  inventar contenido nuevo, incluso si nunca vio ese input exacto en el
  dataset de entrenamiento.

Se ejecuta como script para entrenar y guardar los pesos en
modelo_correccion.pt. Las clases (Encoder, Attention, Decoder) y la función
de inferencia `corregir_frase` se importan desde funciones.py para servir el
modelo en la API.
"""

import json
import re
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from collections import Counter

from conjugacion import (
    componer_clausula, conjugaciones, es_adjetivo, es_infinitivo, es_verbo,
    infinitivo_sin_gobierno, pos_palabra, tiene_verbo_conjugado,
)

from gramatica import (
    lema, lemas_y_formas, es_permitida, cubre_entrada, bien_formada, palabras_obligatorias, token_cubre,
    concuerda, flexionar, formas, lexico_genero, verbo_tras_preposicion, rasgos_adjetivo,
    CONJUNCIONES, FUNCIONALES,
)

random.seed(42)
torch.manual_seed(42)

DEVICE = torch.device("cpu")

PAD, SOS, EOS, UNK = "<pad>", "<sos>", "<eos>", "<unk>"
FIN_DE_FRASE = {".", "!", "?"}

HIDDEN_SIZE = 128
EMB_SIZE = 64
DROPOUT = 0.2
MAX_LEN_SALIDA = 32  # tope de tokens al generar, evita loops infinitos (las
                      # frases de 10 palabras llegan a ~25 tokens de salida)
BEAM = 5             # hipótesis que se mantienen en paralelo al generar

# ── Tokenización de la frase de salida ──────────────────────────────────────
# Separamos palabras y signos de puntuación como tokens distintos para que el
# vocabulario de salida no explote (p. ej. "agua" y "agua." serían el mismo).

def tokenizar_salida(texto):
    return re.findall(r"\w+|[^\w\s]", texto, flags=re.UNICODE)

def detokenizar_salida(tokens):
    no_espacio_antes = set(".,;:!?)»”’")
    no_espacio_despues = set("¿¡(«“‘")
    texto = ""
    for tok in tokens:
        if not texto:
            texto = tok
        elif tok in no_espacio_antes or texto[-1] in no_espacio_despues:
            texto += tok
        else:
            texto += " " + tok
    return texto

# ── Vocabulario de salida ────────────────────────────────────────────────────

class Vocabulario:
    def __init__(self, oraciones_tokenizadas):
        especiales = [PAD, SOS, EOS, UNK]
        vistos = set()
        palabras = []
        for tokens in oraciones_tokenizadas:
            for t in tokens:
                if t not in vistos:
                    vistos.add(t)
                    palabras.append(t)
        self.idx2tok = especiales + sorted(palabras)
        self.tok2idx = {t: i for i, t in enumerate(self.idx2tok)}
        # género/número de cada sustantivo según el dataset (ver
        # gramatica.lexico_genero); se guarda en el checkpoint.
        self.generos = lexico_genero(oraciones_tokenizadas)

    def __len__(self):
        return len(self.idx2tok)

    def encode(self, tokens):
        unk = self.tok2idx[UNK]
        ids = [self.tok2idx.get(t, unk) for t in tokens]
        return [self.tok2idx[SOS]] + ids + [self.tok2idx[EOS]]

    def decode(self, ids):
        tokens = []
        for i in ids:
            tok = self.idx2tok[i]
            if tok == EOS:
                break
            if tok in (SOS, PAD):
                continue
            tokens.append(tok)
        return tokens

# ── Vectorización de la entrada con spaCy ────────────────────────────────────

_cache_vectores = {}

def vector_palabra(nlp, palabra):
    palabra = palabra.lower()
    if palabra not in _cache_vectores:
        _cache_vectores[palabra] = nlp(palabra).vector.astype(np.float32)
    return _cache_vectores[palabra]

def vectorizar_entrada(nlp, palabras):
    """Convierte una lista de palabras sueltas en una matriz (largo, dim_spacy)."""
    return np.stack([vector_palabra(nlp, p) for p in palabras])

# ── Arquitectura ─────────────────────────────────────────────────────────────
# Encoder bidireccional de una capa: el usuario elige las palabras en cualquier
# orden, y con una sola dirección la representación de cada palabra solo
# "veía" las anteriores, lo que en frases largas hacía que el decoder perdiera
# el contexto de las últimas. Cada dirección usa hidden_size/2, así las salidas
# y el estado inicial del decoder siguen siendo de tamaño hidden_size.

class Encoder(nn.Module):
    def __init__(self, input_size, hidden_size=HIDDEN_SIZE, dropout=DROPOUT):
        super().__init__()
        self.hidden_size = hidden_size
        self.gru = nn.GRU(input_size, hidden_size // 2, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, lengths):
        x = self.dropout(x)
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths, batch_first=True, enforce_sorted=False
        )
        outputs, hidden = self.gru(packed)
        outputs, _ = nn.utils.rnn.pad_packed_sequence(outputs, batch_first=True)
        # (2, batch, h/2) -> (1, batch, h): estados finales de ambas direcciones
        hidden = torch.cat([hidden[0], hidden[1]], dim=1).unsqueeze(0)
        return outputs, hidden

class Attention(nn.Module):
    def __init__(self, hidden_size=HIDDEN_SIZE):
        super().__init__()
        self.attn = nn.Linear(hidden_size * 2, hidden_size)
        self.v = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, decoder_hidden, encoder_outputs, mask):
        seq_len = encoder_outputs.size(1)
        dec_h = decoder_hidden.squeeze(0).unsqueeze(1).repeat(1, seq_len, 1)
        energia = torch.tanh(self.attn(torch.cat([dec_h, encoder_outputs], dim=2)))
        scores = self.v(energia).squeeze(2)
        scores = scores.masked_fill(mask == 0, -1e10)
        pesos = F.softmax(scores, dim=1)
        contexto = torch.bmm(pesos.unsqueeze(1), encoder_outputs)
        return contexto, pesos

class Decoder(nn.Module):
    def __init__(self, vocab_size, hidden_size=HIDDEN_SIZE, emb_size=EMB_SIZE, dropout=DROPOUT):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_size, padding_idx=0)
        self.attention = Attention(hidden_size)
        self.gru = nn.GRU(emb_size + hidden_size, hidden_size, batch_first=True)
        self.out = nn.Linear(hidden_size * 2 + emb_size, vocab_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, token_entrada, hidden, encoder_outputs, mask):
        embedded = self.dropout(self.embedding(token_entrada).unsqueeze(1))
        contexto, pesos = self.attention(hidden, encoder_outputs, mask)
        entrada_gru = torch.cat([embedded, contexto], dim=2)
        salida, hidden = self.gru(entrada_gru, hidden)
        logits = self.out(torch.cat([salida.squeeze(1), contexto.squeeze(1), embedded.squeeze(1)], dim=1))
        return logits, hidden, pesos

# ── Restricción de vocabulario en inferencia ─────────────────────────────────

def _mascara_vocabulario(nlp, vocab_salida, palabras):
    """Devuelve un tensor (vocab,) con 0.0 en los tokens que el decoder tiene
    permitido generar y -inf en el resto: palabras funcionales cerradas
    (gramatica.FUNCIONALES), puntuación, <eos>, y cualquier token cuyo lema
    coincida con el de alguna palabra de entrada. Esto es lo que impide que
    el modelo "invente" contenido que el usuario no seleccionó, incluso para
    combinaciones de palabras que nunca vio en el dataset de entrenamiento."""
    lemas_entrada = lemas_y_formas(nlp, palabras)
    mask = torch.full((len(vocab_salida),), float("-inf"))
    for idx, tok in enumerate(vocab_salida.idx2tok):
        if tok in (PAD, SOS, UNK):
            continue
        if tok == EOS:
            mask[idx] = 0.0
            continue
        if es_permitida(nlp, tok, lemas_entrada):
            mask[idx] = 0.0
    return mask

# ── Inferencia (usada acá para evaluar y en funciones.py para servir) ────────

def corregir_frase(nlp, encoder, decoder, vocab_salida, palabras):
    """Arma una frase gramaticalmente correcta en español a partir de
    `palabras`, reordenándolas y conjugándolas, pero sin agregar contenido
    que el usuario no seleccionó (ver `_mascara_vocabulario`).

    Si `palabras` tiene un solo elemento no hay nada que corregir ni
    reordenar: se devuelve tal cual. Las palabras que el modelo no conoce se
    reemplazan temporalmente por una conocida equivalente (ver `_reemplazos`).
    Si el modelo no logra usar todas las palabras de una sola vez, se parte la
    frase en tramos, se corrige cada tramo y se unen; un tramo que no se puede
    armar queda literal."""
    palabras = [p.strip() for p in palabras if isinstance(p, str) and p.strip()]
    if len(palabras) <= 1:
        return palabras[0] if palabras else ""
    reemplazos = _reemplazos(nlp, vocab_salida, palabras)
    entrada = tuple(reemplazos[p][0] if p in reemplazos else p for p in palabras)
    frase, _ = _corregir_recursivo(nlp, encoder, decoder, vocab_salida, entrada, False, {})
    return _restaurar(frase, reemplazos) if reemplazos else frase

# ── Palabras fuera del vocabulario ───────────────────────────────────────────
# El decoder solo puede escribir tokens que vio al entrenar: si el usuario
# elige "sillón" o "cenar" y no están en el dataset, no hay forma de que
# aparezcan en la frase y todo cae al armado literal. Para esas palabras se
# usa un "doble": la palabra conocida más parecida (vector de spaCy) de la
# misma categoría y, en sustantivos, del mismo género y número. Se genera la
# frase con el doble y después se vuelve a poner la palabra original con la
# misma flexión que tomó el doble ("comí" -> "cené", "roja" -> "azul").

_cache_candidatos = {}


def _lemas_vocab(nlp, vocab_salida):
    clave = (id(vocab_salida), "lemas")
    if clave not in _cache_candidatos:
        _cache_candidatos[clave] = {lema(nlp, t) for t in vocab_salida.idx2tok if t.isalpha()}
    return _cache_candidatos[clave]


def _conocida(nlp, vocab_salida, p):
    """True si el decoder puede escribir `p` o alguna forma suya: la palabra
    misma, una flexión, o un token cuyo lema sea el de `p` ("doler" está
    como "duele")."""
    pl = p.lower()
    vocab_tokens = vocab_salida.tok2idx
    return (pl in vocab_tokens or any(f in vocab_tokens for f in formas(pl))
            or lema(nlp, pl) in _lemas_vocab(nlp, vocab_salida))


def _categoria(nlp, p):
    if es_infinitivo(nlp, p):
        return "verbo"
    if es_adjetivo(nlp, p):
        return "adj"
    if pos_palabra(nlp, p) in ("NOUN", "PROPN"):
        return "sust"
    return pos_palabra(nlp, p) or "otro"


def _rasgos_sustantivo(nlp, s):
    """(género, número) estimado de un sustantivo que no está en el léxico."""
    n = "p" if s.endswith("s") and not s.endswith(("és", "ís", "ús")) else "s"
    base = s[:-1] if n == "p" else s
    doc = nlp(base)
    g = doc[0].morph.get("Gender") if len(doc) else []
    if g:
        return ("f" if g[0] == "Fem" else "m"), n
    return ("f" if base.endswith(("a", "ión", "dad", "tad", "tud", "umbre")) else "m"), n


def _candidatos(nlp, vocab_salida, categoria):
    clave = (id(vocab_salida), categoria)
    if clave not in _cache_candidatos:
        toks = [t for t in vocab_salida.idx2tok if t.isalpha() and t.islower() and t not in FUNCIONALES]
        if categoria == "verbo":
            cands = [t for t in toks if es_infinitivo(nlp, t)]
        elif categoria == "adj":
            # forma base: masculino singular o invariable ("rojo", "azul")
            cands = [t for t in toks if es_adjetivo(nlp, t) and not t.endswith(("a", "s"))]
        elif categoria == "sust":
            cands = [t for t in toks if t in vocab_salida.generos]
        else:
            cands = [t for t in toks if pos_palabra(nlp, t) == categoria]
        matriz = np.stack([vector_palabra(nlp, t) for t in cands]) if cands else None
        if matriz is not None:
            matriz = matriz / (np.linalg.norm(matriz, axis=1, keepdims=True) + 1e-8)
        _cache_candidatos[clave] = (cands, matriz)
    return _cache_candidatos[clave]


def _reemplazos(nlp, vocab_salida, palabras):
    """{palabra desconocida: (doble, categoría)} para la entrada."""
    prohibidas = lemas_y_formas(nlp, palabras)
    reemplazos = {}
    for p in palabras:
        pl = p.lower()
        if pl in FUNCIONALES or pl in CONJUNCIONES or not pl.isalpha() or p in reemplazos:
            continue
        if _conocida(nlp, vocab_salida, pl):
            continue
        cat = _categoria(nlp, pl)
        cands, matriz = _candidatos(nlp, vocab_salida, cat)
        if not cands:
            continue
        rasgos = _rasgos_sustantivo(nlp, pl) if cat == "sust" else None
        v = vector_palabra(nlp, pl)
        sims = matriz @ (v / (np.linalg.norm(v) + 1e-8))
        for i in np.argsort(-sims):
            c = cands[i]
            if c in prohibidas or any(c == r[0] for r in reemplazos.values()):
                continue
            if rasgos and rasgos not in vocab_salida.generos[c]:
                continue
            reemplazos[p] = (c, cat)
            prohibidas |= formas(c) | {c}
            break
    return reemplazos


def _restaurar(frase, reemplazos):
    """Vuelve a poner en `frase` las palabras originales en lugar de sus
    dobles, con la misma flexión que tomó cada doble."""
    mapa = {}
    for original, (doble, cat) in reemplazos.items():
        o = original.lower()
        mapa[doble] = o
        if cat == "verbo":
            conj_o = conjugaciones(o)
            for tag, forma in conjugaciones(doble).items():
                mapa.setdefault(forma, conj_o.get(tag, o))
        elif cat == "adj":
            for forma in formas(doble):
                g, n = rasgos_adjetivo(forma)
                mapa.setdefault(forma, flexionar(o, g or "m", n))
    tokens = []
    for tok in tokenizar_salida(frase):
        nuevo = mapa.get(tok.lower())
        if nuevo is None:
            tokens.append(tok)
        else:
            tokens.append(nuevo[0].upper() + nuevo[1:] if tok[:1].isupper() else nuevo)
    return detokenizar_salida(tokens)

def _corregir_recursivo(nlp, encoder, decoder, vocab_salida, palabras, causa, memo):
    """Devuelve (frase, palabras_sin_procesar): cuántas palabras quedaron
    literales, sin que el modelo las conjugue. Se usa para elegir el corte que
    mejor aprovecha al modelo. `causa` indica que el tramo viene después de
    "porque" (afecta el tiempo verbal de componer_clausula)."""
    clave = (palabras, causa)
    if clave in memo:
        return memo[clave]
    frase = _generar(nlp, encoder, decoder, vocab_salida, list(palabras))
    if frase is None:
        # El modelo no pudo (verbo sin conjugar, palabras que no conoce...):
        # si es una cláusula simple, se arma por reglas conjugando el verbo.
        frase_reglas = componer_clausula(nlp, palabras, causa)
        # Las reglas eligen el artículo con el género que spaCy adivina para
        # la palabra suelta ("el flor"): se valida con el léxico del dataset.
        if frase_reglas is not None and concuerda(tokenizar_salida(frase_reglas), vocab_salida.generos, set()):
            memo[clave] = (frase_reglas, 0)
            return memo[clave]
    # El dataset cubre frases de hasta MAX_PALABRAS_DIRECTO palabras: más
    # largas que eso, aunque el modelo devuelva algo válido, se prefiere
    # partir si todos los tramos pueden armarse con el modelo.
    corte = None
    if len(palabras) >= 4 and (frase is None or len(palabras) > MAX_PALABRAS_DIRECTO):
        corte = _mejor_corte(nlp, encoder, decoder, vocab_salida, palabras, causa, memo)
    if frase is not None and (corte is None or corte[1] > 0):
        resultado = (frase, 0)
    elif corte is not None:
        resultado = corte
    else:
        resultado = (_frase_literal(palabras), len(palabras))
    memo[clave] = resultado
    return resultado

MAX_PALABRAS_DIRECTO = 10

def _mejor_corte(nlp, encoder, decoder, vocab_salida, palabras, causa, memo):
    """Prueba los cortes candidatos y devuelve (frase, palabras_sin_procesar)
    del que deja menos palabras literales."""
    mejor = None
    for izq, conector, der in _cortes(nlp, palabras):
        f_izq, lit_izq = _sub(nlp, encoder, decoder, vocab_salida, izq, causa, memo)
        f_der, lit_der = _sub(nlp, encoder, decoder, vocab_salida, der, conector == "porque", memo)
        union = f" {conector} " if conector else ", "
        candidato = (f_izq.rstrip(".") + union + f_der[0].lower() + f_der[1:], lit_izq + lit_der)
        if mejor is None or candidato[1] < mejor[1]:
            mejor = candidato
        if mejor[1] == 0:
            break
    return mejor

def _sub(nlp, encoder, decoder, vocab_salida, palabras, causa, memo):
    if len(palabras) == 1:
        return _frase_literal(palabras), 1
    return _corregir_recursivo(nlp, encoder, decoder, vocab_salida, palabras, causa, memo)

MAX_CORTES = 3  # candidatos de corte a probar por tramo (acota la latencia)
NO_SEPARAR_DE = {"querer", "quiero", "poder", "necesitar", "deber", "saber", "soler", "intentar", "ir", "no", "tener"}

def _cortes(nlp, palabras):
    """Candidatos para partir una frase que el modelo no pudo armar entera,
    como (izquierda, conector, derecha), del más al menos prometedor.
    Si hay conjunciones (porque, y, pero...) se corta en ellas y la conjunción
    se conserva como nexo; si no, se corta antes de un verbo o, en su defecto,
    en cualquier posición. En todos los casos, cerca del medio primero."""
    n = len(palabras)
    medio = n / 2
    conj = [i for i in range(1, n - 1) if palabras[i].lower() in CONJUNCIONES]
    if conj:
        orden = sorted(conj, key=lambda k: abs(k - medio))[:MAX_CORTES]
        return [(palabras[:i], palabras[i], palabras[i + 1:]) for i in orden]
    # No cortar entre un modal y su complemento ("querer | ir", "poder | comer")
    posibles = [i for i in range(2, n - 1) if palabras[i - 1].lower() not in NO_SEPARAR_DE]
    verbos = [i for i in posibles if es_verbo(nlp, palabras[i])]
    orden = sorted(verbos, key=lambda k: abs(k - medio))[:MAX_CORTES]
    orden += [i for i in sorted(posibles, key=lambda k: abs(k - medio)) if i not in orden][: MAX_CORTES - len(orden)]
    return [(palabras[:i], None, palabras[i:]) for i in orden]

class _Hipotesis:
    """Una frase parcial del beam search, con el estado de las restricciones
    (qué palabras del usuario faltan usar, cuántas veces se usó cada una...)."""
    __slots__ = ("ids", "logp", "hidden", "restante", "pendientes", "usos_funcionales", "bigramas", "terminada")

    def __init__(self, ids, logp, hidden, restante, pendientes, usos_funcionales, bigramas, terminada=False):
        self.ids, self.logp, self.hidden = ids, logp, hidden
        self.restante, self.pendientes = restante, pendientes
        self.usos_funcionales, self.bigramas = usos_funcionales, bigramas
        self.terminada = terminada

    def puntaje(self):
        # Normalizado por largo: sin esto el beam prefiere frases cortas y
        # "apuradas", justo el problema que tenían las frases largas.
        return self.logp / max(len(self.ids), 1) ** 0.7


def _generar(nlp, encoder, decoder, vocab_salida, palabras, beam=BEAM):
    """Genera la frase con el modelo usando beam search restringido: en cada
    paso solo se expanden tokens permitidos por la máscara de vocabulario, que
    no repitan una palabra del usuario más veces de las que la eligió y que no
    cierren la frase antes de usarlas todas. Al final se devuelve la mejor
    hipótesis que además pase los chequeos de `_valida`, o None si ninguna.

    El greedy anterior se comprometía con una palabra por paso: en frases
    largas, un primer token apenas peor ("Querer" en vez de "Quiero") lo
    dejaba sin salida y había que partir la frase o devolverla literal."""
    encoder.eval()
    decoder.eval()
    eos_idx = vocab_salida.tok2idx[EOS]
    sos_idx = vocab_salida.tok2idx[SOS]
    with torch.no_grad():
        vecs = vectorizar_entrada(nlp, palabras)
        x = torch.tensor(vecs, dtype=torch.float32).unsqueeze(0)
        encoder_outputs, hidden = encoder(x, [len(palabras)])
        mask_vocab = _mascara_vocabulario(nlp, vocab_salida, palabras)

        requeridas = palabras_obligatorias(palabras)
        cubre_cache = {}
        claves = list(dict.fromkeys(requeridas))

        def palabras_que_cubre(tok):
            if tok not in cubre_cache:
                cubre_cache[tok] = [p for p in claves if token_cubre(nlp, tok, p)]
            return cubre_cache[tok]

        # Cada palabra de contenido se puede usar tantas veces como el usuario
        # la eligió (evita "tengo frío, tengo frío"); las funcionales, hasta 2.
        vivas = [_Hipotesis([], 0.0, hidden, dict(Counter(requeridas)), frozenset(requeridas),
                            Counter(), frozenset())]
        terminadas = []
        max_len = min(MAX_LEN_SALIDA, 3 * len(palabras) + 6)
        for _ in range(max_len):
            if not vivas:
                break
            n = len(vivas)
            tokens = torch.tensor([h.ids[-1] if h.ids else sos_idx for h in vivas])
            hid = torch.cat([h.hidden for h in vivas], dim=1)
            enc = encoder_outputs.expand(n, -1, -1)
            logits, hid_nuevo, _ = decoder(tokens, hid, enc, torch.ones(n, enc.size(1)))
            logp = F.log_softmax(logits, dim=1) + mask_vocab

            candidatas = []
            for i, h in enumerate(vivas):
                prev = h.ids[-1] if h.ids else sos_idx
                encontrados = 0
                for cand in torch.argsort(logp[i], descending=True).tolist():
                    valor = logp[i, cand].item()
                    if valor == float("-inf") or encontrados >= beam:
                        break
                    if cand == eos_idx:
                        if h.pendientes:
                            continue  # no se puede terminar sin usar todas las palabras
                        candidatas.append((h.logp + valor, i, cand, None))
                        encontrados += 1
                        continue
                    tok = vocab_salida.idx2tok[cand]
                    if tok in FIN_DE_FRASE and h.pendientes:
                        continue  # no cerrar la frase antes de usar todas las palabras
                    if (prev, cand) in h.bigramas:
                        continue
                    cubre = palabras_que_cubre(tok)
                    if any(h.restante[p] == 0 for p in cubre):
                        continue  # ya se usó todas las veces que el usuario la eligió
                    if not cubre and tok.lower() in FUNCIONALES and h.usos_funcionales[tok.lower()] >= 2:
                        continue
                    candidatas.append((h.logp + valor, i, cand, cubre))
                    encontrados += 1

            candidatas.sort(key=lambda c: c[0], reverse=True)
            nuevas = []
            for logp_total, i, cand, cubre in candidatas:
                if len(nuevas) >= beam:
                    break
                h = vivas[i]
                if cand == eos_idx:
                    terminadas.append(_Hipotesis(h.ids, logp_total, None, h.restante, h.pendientes,
                                                 h.usos_funcionales, h.bigramas, True))
                    continue
                tok = vocab_salida.idx2tok[cand]
                restante = dict(h.restante)
                for p in cubre:
                    restante[p] -= 1
                usos = h.usos_funcionales
                if not cubre and tok.lower() in FUNCIONALES:
                    usos = Counter(usos)
                    usos[tok.lower()] += 1
                prev = h.ids[-1] if h.ids else sos_idx
                nueva = _Hipotesis(h.ids + [cand], logp_total, hid_nuevo[:, i:i + 1].contiguous(), restante,
                                   h.pendientes - set(cubre), usos, h.bigramas | {(prev, cand)})
                if tok in FIN_DE_FRASE:
                    # la frase termina en el primer punto: nada de texto extra
                    nueva.terminada = True
                    terminadas.append(nueva)
                else:
                    nuevas.append(nueva)
            vivas = nuevas
            # Ya hay `beam` frases completas mejores que cualquier parcial viva:
            # seguir expandiendo solo puede empeorarlas (logp es acumulativo).
            if len(terminadas) >= beam and vivas:
                peor = sorted(h.puntaje() for h in terminadas)[-beam]
                if max(h.logp for h in vivas) / max_len ** 0.7 < peor:
                    break

        adjetivos = set()
        for p in palabras:
            if es_adjetivo(nlp, p):
                adjetivos |= formas(p)
        for h in sorted(terminadas, key=lambda h: h.puntaje(), reverse=True):
            frase = _valida(nlp, vocab_salida.decode(h.ids), palabras, vocab_salida.generos, adjetivos)
            if frase is not None:
                return frase
        return None


def _valida(nlp, tokens, palabras, generos, adjetivos):
    """La frase detokenizada si `tokens` sirve como respuesta, o None."""
    # Si el modelo no usó todas las palabras del usuario (típico en frases
    # largas o con palabras que nunca vio), su salida no es confiable:
    # mejor no devolverla que devolver una frase con contenido perdido.
    if not tokens or not cubre_entrada(nlp, tokens, palabras) or not bien_formada(tokens):
        return None
    # Errores de concordancia ("el flor", "un sándwich rica") o un verbo
    # conjugado donde va el infinitivo ("a corrí"): se prueba la siguiente
    # hipótesis del beam, que suele ser la misma frase bien concordada.
    if not concuerda(tokens, generos, adjetivos) or verbo_tras_preposicion(tokens, palabras):
        return None
    frase = detokenizar_salida(tokens)
    # Si el usuario eligió un verbo en infinitivo, la frase tiene que
    # tener algún verbo conjugado ("No esta noche dormir." no sirve).
    infinitivos = {p.lower() for p in palabras if es_infinitivo(nlp, p)}
    if infinitivos:
        if not tiene_verbo_conjugado(nlp, frase) or infinitivo_sin_gobierno(nlp, frase, infinitivos):
            return None
    return frase

def _frase_literal(palabras):
    """Fallback determinista: exactamente las palabras recibidas, en el orden
    recibido, sin agregar nada salvo mayúscula inicial y punto final."""
    texto = " ".join(palabras)
    return texto[0].upper() + texto[1:] + "."

# ── Entrenamiento ─────────────────────────────────────────────────────────────

def _pares_compuestos(pares, cantidad):
    """Genera ejemplos largos uniendo dos pares (entrada, salida) del dataset:
    entrada = palabras de A + conector (si es una palabra) + palabras de B;
    salida = A sin punto + conector + B con minúscula inicial."""
    simples = [
        (pin, pout) for pin, pout in pares
        if len(pin) <= 5 and pout[-1] == "." and pout[0].isalpha() and "¿" not in pout
    ]
    conectores = [("y", ["y"], ["y"]), ("porque", ["porque"], ["porque"]), (",", [], [","])]
    pesos = [0.4, 0.3, 0.3]
    compuestos = []
    intentos = 0
    while len(compuestos) < cantidad and intentos < cantidad * 20:
        intentos += 1
        (a_in, a_out), (b_in, b_out) = random.sample(simples, 2)
        _, extra_in, extra_out = random.choices(conectores, pesos)[0]
        if "porque" in a_in or "porque" in b_in or set(a_in) & set(b_in):
            continue
        entrada = a_in + extra_in + b_in
        if len(entrada) > 10:
            continue
        salida = a_out[:-1] + extra_out + [b_out[0].lower()] + b_out[1:]
        compuestos.append((entrada, salida))
    return compuestos

def entrenar():
    import spacy

    print("Cargando spaCy...")
    nlp = spacy.load("es_core_news_md")
    dim_spacy = nlp.vocab.vectors_length or len(nlp("agua").vector)
    print(f"spaCy cargado (dim={dim_spacy})\n")

    print("Cargando dataset...")
    pares = []
    with open("dataset_correccion.jsonl", "r", encoding="utf-8") as f:
        for linea in f:
            par = json.loads(linea)
            pares.append((par["input"].split(), tokenizar_salida(par["output"])))
    print(f"Pares cargados: {len(pares)}")

    # Solo se entrena con ejemplos que usan TODAS las palabras de la entrada:
    # los que descartan palabras le enseñarían al modelo justo lo que la API
    # no debe hacer (ver gramatica.cubre_entrada).
    pares = [(pin, pout) for pin, pout in pares if cubre_entrada(nlp, pout, pin)]
    print(f"Pares que respetan todas las palabras: {len(pares)}")

    # Aumentación: además de las frases largas del dataset (frases_largas.py),
    # se unen dos pares reales con "y", "porque" o coma, conservando el orden
    # de cada cláusula, para que el modelo vea uniones entre cláusulas libres.
    pares += _pares_compuestos(pares, cantidad=1500)
    print(f"Con frases compuestas: {len(pares)}\n")

    vocab_salida = Vocabulario([out for _, out in pares])
    print(f"Vocabulario de salida: {len(vocab_salida)} tokens\n")

    print("Vectorizando entradas con spaCy (con caché por palabra)...")
    ejemplos = []
    for palabras_in, tokens_out in pares:
        vecs = vectorizar_entrada(nlp, palabras_in)
        ids_out = vocab_salida.encode(tokens_out)
        ejemplos.append((vecs, ids_out, tuple(tokens_out)))
    print(f"Palabras únicas vectorizadas: {len(_cache_vectores)}\n")

    # Validación por FRASE, no por par: cada frase aparece con varias
    # permutaciones de la entrada, y si se reparten al azar el val_loss mide
    # memoria (frases que ya vio en train), no generalización a frases nuevas.
    frases = sorted({e[2] for e in ejemplos})
    random.shuffle(frases)
    frases_val = set(frases[: len(frases) // 10])
    train_set = [(v, i) for v, i, f in ejemplos if f not in frases_val]
    val_set = [(v, i) for v, i, f in ejemplos if f in frases_val]
    print(f"Train: {len(train_set)} | Val: {len(val_set)} ({len(frases_val)} frases no vistas)\n")

    encoder = Encoder(dim_spacy).to(DEVICE)
    decoder = Decoder(len(vocab_salida)).to(DEVICE)
    optimizador = torch.optim.Adam(
        list(encoder.parameters()) + list(decoder.parameters()), lr=1e-3
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizador, mode="min", factor=0.5, patience=4
    )
    pad_idx = vocab_salida.tok2idx[PAD]
    criterio = nn.CrossEntropyLoss(ignore_index=pad_idx, label_smoothing=0.1)

    def hacer_batch(muestras):
        muestras = sorted(muestras, key=lambda m: len(m[0]), reverse=True)
        lengths_in = [len(m[0]) for m in muestras]
        max_in = max(lengths_in)
        max_out = max(len(m[1]) for m in muestras)

        batch_x = np.zeros((len(muestras), max_in, dim_spacy), dtype=np.float32)
        batch_y = np.full((len(muestras), max_out), pad_idx, dtype=np.int64)
        for i, (vecs, ids_out) in enumerate(muestras):
            batch_x[i, : len(vecs)] = vecs
            batch_y[i, : len(ids_out)] = ids_out

        x = torch.tensor(batch_x)
        y = torch.tensor(batch_y)
        mask = torch.zeros(len(muestras), max_in)
        for i, l in enumerate(lengths_in):
            mask[i, :l] = 1
        return x, lengths_in, mask, y

    EPOCHS = 60
    BATCH_SIZE = 64
    TEACHER_FORCING = 0.5
    PACIENCIA = 10   # epochs sin mejorar val_loss antes de cortar

    print("Entrenando...")
    mejor_val_loss = float("inf")
    sin_mejora = 0
    for epoch in range(1, EPOCHS + 1):
        encoder.train()
        decoder.train()
        random.shuffle(train_set)
        loss_total = 0.0

        for i in range(0, len(train_set), BATCH_SIZE):
            batch = train_set[i : i + BATCH_SIZE]
            x, lengths_in, mask, y = hacer_batch(batch)

            optimizador.zero_grad()
            encoder_outputs, hidden = encoder(x, lengths_in)

            token = y[:, 0]  # <sos>
            loss = 0.0
            pasos = y.size(1) - 1
            for t in range(1, y.size(1)):
                logits, hidden, _ = decoder(token, hidden, encoder_outputs, mask)
                loss = loss + criterio(logits, y[:, t])
                usar_teacher = random.random() < TEACHER_FORCING
                token = y[:, t] if usar_teacher else logits.argmax(1)

            loss = loss / pasos
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(encoder.parameters()) + list(decoder.parameters()), 1.0
            )
            optimizador.step()
            loss_total += loss.item() * len(batch)

        loss_train = loss_total / len(train_set)

        encoder.eval()
        decoder.eval()
        with torch.no_grad():
            val_loss_total = 0.0
            for i in range(0, len(val_set), BATCH_SIZE):
                batch = val_set[i : i + BATCH_SIZE]
                x, lengths_in, mask, y = hacer_batch(batch)
                encoder_outputs, hidden = encoder(x, lengths_in)
                token = y[:, 0]
                loss = 0.0
                pasos = y.size(1) - 1
                for t in range(1, y.size(1)):
                    logits, hidden, _ = decoder(token, hidden, encoder_outputs, mask)
                    loss = loss + criterio(logits, y[:, t])
                    token = logits.argmax(1)
                val_loss_total += (loss.item() / pasos) * len(batch)
            loss_val = val_loss_total / max(len(val_set), 1)

        scheduler.step(loss_val)

        lr_actual = optimizador.param_groups[0]["lr"]
        print(f"Epoch {epoch:3d} | train_loss={loss_train:.4f} | val_loss={loss_val:.4f} | lr={lr_actual:.2e}", flush=True)

        if loss_val >= mejor_val_loss:
            sin_mejora += 1
            if sin_mejora >= PACIENCIA:
                print(f"Sin mejora en {PACIENCIA} epochs, se corta el entrenamiento.")
                break
        else:
            sin_mejora = 0
            mejor_val_loss = loss_val
            torch.save(
                {
                    "encoder_state": encoder.state_dict(),
                    "decoder_state": decoder.state_dict(),
                    "tok2idx": vocab_salida.tok2idx,
                    "idx2tok": vocab_salida.idx2tok,
                    "generos": vocab_salida.generos,
                    "dim_spacy": dim_spacy,
                    "hidden_size": HIDDEN_SIZE,
                    "emb_size": EMB_SIZE,
                },
                "modelo_correccion.pt",
            )

    print(f"\nMejor val_loss: {mejor_val_loss:.4f}")
    print("Modelo guardado en modelo_correccion.pt\n")

    # ── Prueba rápida con frases variadas (algunas no vistas en el dataset) ──
    print("-- Prueba de correccion --")
    checkpoint = torch.load("modelo_correccion.pt", weights_only=False)
    vocab_final = Vocabulario([])
    vocab_final.tok2idx = checkpoint["tok2idx"]
    vocab_final.idx2tok = checkpoint["idx2tok"]
    vocab_final.generos = checkpoint["generos"]
    encoder_final = Encoder(dim_spacy)
    decoder_final = Decoder(len(vocab_final))
    encoder_final.load_state_dict(checkpoint["encoder_state"])
    decoder_final.load_state_dict(checkpoint["decoder_state"])

    ejemplos_prueba = [
        ["mamá", "agua", "querer"],
        ["doler", "cabeza"],
        ["escuela", "no", "querer", "ir"],
        ["amigo", "jugar", "querer", "parque"],
        ["yo", "querer", "comer", "pizza", "noche"],
        ["triste", "estar", "hoy"],
        ["querer", "ir", "parque", "hermano", "jugar", "pelota"],
        ["no", "poder", "dormir", "porque", "tener", "miedo", "oscuridad", "noche"],
        ["mañana", "querer", "ir", "playa", "familia", "nadar", "mar", "porque", "hacer", "calor"],
        ["agua"],
    ]
    for palabras in ejemplos_prueba:
        frase = corregir_frase(nlp, encoder_final, decoder_final, vocab_final, palabras)
        print(f"{palabras} -> {frase}")

if __name__ == "__main__":
    entrenar()
