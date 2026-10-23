"""
Corrección de frases (/corregir).

El usuario manda una frase casi correcta, palabra por palabra ("quiero ir
parque", "mi mamá está cansado", "necesito ayuda con tarea") y la API
devuelve la misma frase con correcciones MÍNIMAS: "Quiero ir al parque.",
"Mi mamá está cansada.", "Necesito ayuda con la tarea."

Cómo funciona: un etiquetador de ediciones (idea de GECToR, "Tag, not
rewrite"). Para cada palabra de la entrada, una red BiGRU chica predice:
  1. qué palabra funcional falta ANTES de ella (nada, "el", "a la", "de",
     "que", una coma...: una lista cerrada aprendida del corpus), y
  2. qué hacer con la palabra: dejarla igual, cambiarle género/número
     (concordancia), cambiarle la persona al verbo ("yo quiere" -> "quiero"),
     ponerle la tilde, cambiar una preposición o borrar una palabra funcional
     sobrante ("la mi casa").
Además predice si la frase es una pregunta (¿...?).

Garantías de diseño (lo que hace que nunca devuelva algo sin sentido):
- La salida siempre son las palabras del usuario, EN SU ORDEN. El modelo no
  puede reordenar ni escribir palabras de contenido nuevas: solo insertar
  palabras funcionales de una lista cerrada o devolver otra forma de la misma
  palabra (generada por reglas en morfologia.py).
- Solo se aplica una edición si el modelo está muy seguro (umbrales); ante
  la duda la palabra queda como la escribió el usuario.
- Las ediciones se validan con reglas estructurales (no dos artículos
  seguidos, no terminar en preposición...) y hay un tope de ediciones por
  frase. Si algo no cierra, se devuelve la frase del usuario solo con
  mayúscula inicial y puntuación final.

La red se entrenó con scripts/entrenar_correccion.py (PyTorch) pero acá corre
en numpy puro: no hace falta torch en producción y tarda pocos milisegundos.
"""

import json
import re

import numpy as np
from spacy.tokens import Doc

from morfologia import (
    DETERMINANTES, PERSONAS, IndiceVerbal, flexionar_adjetivo, flexionar_determinante,
    quitar_tildes, tiene_tilde,
)

# ── Etiquetas ─────────────────────────────────────────────────────────────────

NADA = ""   # etiqueta de inserción "no insertar nada"
PREPOSICIONES_REEMPLAZABLES = ["a", "en", "de", "con", "para", "por"]
TRANSFORMACIONES = (
    ["KEEP"]
    + [f"AGR_{g}{n}" for g in "mf" for n in "sp"]
    + [f"V_{p}" for p in PERSONAS]
    + ["ACC", "DEL"]
    + [f"REPL_{p}" for p in PREPOSICIONES_REEMPLAZABLES]
)
TIPOS_FRASE = ["declarativa", "pregunta", "exclamacion"]

# Palabras funcionales que se pueden borrar si sobran (nunca contenido).
BORRABLES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "al", "del", "a", "de", "en",
    "con", "para", "por", "que", "y", "lo", "le", "se", "me",
}
INTERROGATIVOS = {"qué", "cómo", "dónde", "cuándo", "cuánto", "cuánta", "cuántos", "cuántas",
                  "quién", "quiénes", "cuál", "cuáles", "adónde"}
ARTICULOS_Y_DET = set(DETERMINANTES) - {"al", "del"}
PREPOSICIONES = {"a", "ante", "bajo", "con", "contra", "de", "desde", "en", "entre", "hacia",
                 "hasta", "para", "por", "según", "sin", "sobre", "tras", "al", "del"}

# ── Rasgos por palabra (compartidos con el script de entrenamiento) ──────────

POS_TAGS = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON",
            "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X", "SPACE"]
RASGOS_MORF = {
    "Gender": ["Masc", "Fem"], "Number": ["Sing", "Plur"], "Person": ["1", "2", "3"],
    "VerbForm": ["Fin", "Inf", "Ger", "Part"], "Tense": ["Pres", "Past", "Imp", "Fut"],
    "Mood": ["Ind", "Sub", "Cnd", "Imp"],
    "PronType": ["Art", "Prs", "Dem", "Int", "Ind", "Tot", "Neg", "Rel"], "Definite": ["Def", "Ind"],
}
N_LEXICO = 8
DIM_RASGOS = len(POS_TAGS) + sum(len(v) for v in RASGOS_MORF.values()) + N_LEXICO
TIEMPO_SPACY = {"Pres": "pres", "Past": "pret", "Imp": "imp", "Fut": "fut"}
PIPES_RASGOS = ["tok2vec", "morphologizer", "attribute_ruler"]


def sufijo(palabra):
    return palabra[-3:]


def rasgos_doc(doc, lexico, indice):
    """Matriz (n_palabras, DIM_RASGOS): POS + morfología de spaCy + rasgos de
    léxico (género conocido del sustantivo, si la palabra tiene variante con
    tilde, si es un verbo conjugado conocido...)."""
    generos = lexico["genero"]
    acentos = lexico["acentos"]
    m = np.zeros((len(doc), DIM_RASGOS), dtype=np.float32)
    for i, t in enumerate(doc):
        col = 0
        if t.pos_ in POS_TAGS:
            m[i, POS_TAGS.index(t.pos_)] = 1
        col += len(POS_TAGS)
        morph = t.morph
        for rasgo, valores in RASGOS_MORF.items():
            vals = morph.get(rasgo)
            if vals and vals[0] in valores:
                m[i, col + valores.index(vals[0])] = 1
            col += len(valores)
        w = t.text.lower()
        g = generos.get(w)
        m[i, col + 0] = 1.0 if g == "m" else 0.0
        m[i, col + 1] = 1.0 if g == "f" else 0.0
        m[i, col + 2] = 1.0 if (not tiene_tilde(w) and quitar_tildes(w) in acentos) else 0.0
        m[i, col + 3] = 1.0 if indice.analizar(w) else 0.0
        m[i, col + 4] = 1.0 if w in DETERMINANTES else 0.0
        m[i, col + 5] = 1.0 if w in PREPOSICIONES else 0.0
        m[i, col + 6] = 1.0 if i == 0 else 0.0
        m[i, col + 7] = 1.0 if i == len(doc) - 1 else 0.0
    return m


def ids_doc(doc, vocab_palabras, vocab_sufijos):
    unk = 1
    palabras = np.array([vocab_palabras.get(t.text.lower(), unk) for t in doc], dtype=np.int64)
    sufijos = np.array([vocab_sufijos.get(sufijo(t.text.lower()), unk) for t in doc], dtype=np.int64)
    return palabras, sufijos


def vectores_doc(doc, nlp):
    """Vectores estáticos de spaCy (300 dims) por palabra, sin tocar el vocab."""
    tabla = nlp.vocab.vectors
    out = np.zeros((len(doc), tabla.shape[1]), dtype=np.float32)
    for i, t in enumerate(doc):
        fila = tabla.key2row.get(nlp.vocab.strings[t.text.lower()])
        if fila is not None:
            out[i] = tabla.data[fila]
    return out


def doc_desde_palabras(nlp, palabras):
    """Doc de spaCy con EXACTAMENTE estas palabras (sin re-tokenizar), con POS
    y morfología. Se usa igual al entrenar y en producción."""
    doc = Doc(nlp.vocab, words=palabras)
    for nombre in PIPES_RASGOS:
        doc = nlp.get_pipe(nombre)(doc)
    return doc


# ── Red en numpy ──────────────────────────────────────────────────────────────

def _sigmoide(x):
    return 1.0 / (1.0 + np.exp(-x))


def _gru(x, w_ih, w_hh, b_ih, b_hh, reverso):
    """GRU de PyTorch (orden de compuertas r, z, n) sobre x: (T, entrada)."""
    T = x.shape[0]
    H = w_hh.shape[1]
    gi = x @ w_ih.T + b_ih
    h = np.zeros(H, dtype=np.float32)
    salida = np.zeros((T, H), dtype=np.float32)
    pasos = range(T - 1, -1, -1) if reverso else range(T)
    for t in pasos:
        gh = w_hh @ h + b_hh
        r = _sigmoide(gi[t, :H] + gh[:H])
        z = _sigmoide(gi[t, H:2 * H] + gh[H:2 * H])
        n = np.tanh(gi[t, 2 * H:] + r * gh[2 * H:])
        h = (1 - z) * n + z * h
        salida[t] = h
    return salida


def _softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


class RedEdiciones:
    """Misma arquitectura que ModeloEdiciones en scripts/entrenar_correccion.py."""

    def __init__(self, pesos):
        self.p = {k: pesos[k].astype(np.float32) for k in pesos.files}
        self.capas = int(max(int(k.split("_l")[1].split("_")[0]) for k in self.p if k.startswith("gru.weight_ih_l")) + 1)

    def __call__(self, palabras, sufijos, vectores, rasgos):
        p = self.p
        x = np.concatenate([
            p["emb_palabra.weight"][palabras],
            p["emb_sufijo.weight"][sufijos],
            vectores @ p["proy_vector.weight"].T,
            rasgos,
        ], axis=1)
        x = np.tanh(x @ p["entrada.weight"].T + p["entrada.bias"])
        for capa in range(self.capas):
            ida = _gru(x, p[f"gru.weight_ih_l{capa}"], p[f"gru.weight_hh_l{capa}"],
                       p[f"gru.bias_ih_l{capa}"], p[f"gru.bias_hh_l{capa}"], False)
            vuelta = _gru(x, p[f"gru.weight_ih_l{capa}_reverse"], p[f"gru.weight_hh_l{capa}_reverse"],
                          p[f"gru.bias_ih_l{capa}_reverse"], p[f"gru.bias_hh_l{capa}_reverse"], True)
            x = np.concatenate([ida, vuelta], axis=1)
        ins = _softmax(x @ p["cabeza_ins.weight"].T + p["cabeza_ins.bias"])
        tr = _softmax(x @ p["cabeza_tr.weight"].T + p["cabeza_tr.bias"])
        frase = np.concatenate([x.mean(axis=0), x.max(axis=0)])
        tipo = _softmax(frase @ p["cabeza_tipo.weight"].T + p["cabeza_tipo.bias"])
        return ins, tr, tipo


# ── Entrada y salida de texto ─────────────────────────────────────────────────

_SIGNOS = "¿?¡!.,;:\"'()[]{}«»“”…-"


def normalizar_entrada(palabras):
    """Lista del back -> (tokens originales, pregunta?, exclamación?).
    Cada elemento puede traer varias palabras ("por favor") o puntuación."""
    tokens, pregunta, exclamacion = [], False, False
    for p in palabras:
        if not isinstance(p, str):
            continue
        pregunta |= "?" in p or "¿" in p
        exclamacion |= "!" in p or "¡" in p
        for parte in p.split():
            limpia = parte.strip(_SIGNOS)
            if limpia:
                tokens.append(limpia)
    return tokens, pregunta, exclamacion


def _contracciones(tokens):
    """a + el -> al, de + el -> del (salvo 'él' pronombre o 'El' nombre propio)."""
    salida = []
    for t in tokens:
        if salida and t == "el" and salida[-1].lower() in ("a", "de"):
            salida[-1] = salida[-1] + "l"
            continue
        salida.append(t)
    return salida


def _conjunciones_eufonicas(tokens):
    """'y' -> 'e' ante i-/hi- ("padres e hijos"), 'o' -> 'u' ante o-/ho-."""
    out = list(tokens)
    for i in range(len(out) - 1):
        sig = quitar_tildes(out[i + 1].lower())
        if out[i] == "y" and (sig.startswith("i") or (sig.startswith("hi") and not sig.startswith(("hie", "hia")))):
            out[i] = "e"
        elif out[i] == "o" and (sig.startswith("o") or sig.startswith("ho")):
            out[i] = "u"
    return out


def armar_texto(tokens, tipo):
    texto = ""
    for t in tokens:
        if t == ",":
            texto = texto.rstrip(",") + ","
        else:
            texto = (texto + " " + t) if texto else t
    texto = texto.strip(" ,")
    if not texto:
        return ""
    texto = texto[0].upper() + texto[1:]
    if tipo == "pregunta":
        return "¿" + texto + "?"
    if tipo == "exclamacion":
        return "¡" + texto + "!"
    return texto + "."


ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
NO_PUEDEN_CERRAR = ARTICULOS | {"mi", "mis", "tu", "tus", "su", "sus", "al", "del"} | (PREPOSICIONES - {"según"})


def problemas(tokens):
    """Cantidad de problemas estructurales de una frase: artículo o
    preposición colgando al final ("voy a la"), dos artículos seguidos ("la
    el"), preposiciones seguidas ("en con"), palabras funcionales repetidas
    ("de de"), comas mal puestas."""
    toks = [t.lower() for t in tokens]
    n = 0
    for i, t in enumerate(toks):
        sig = toks[i + 1] if i + 1 < len(toks) else None
        if t in NO_PUEDEN_CERRAR and (sig is None or sig == ","):
            n += 1
        if t == "," and (i == 0 or sig is None or sig == "," or toks[i - 1] in PREPOSICIONES | ARTICULOS):
            n += 1
        if t in ARTICULOS and sig in ARTICULOS_Y_DET | PREPOSICIONES | {"que", "y", "o", "me", "te", "se", "nos"}:
            n += 1
        if t in PREPOSICIONES and t != "de" and sig in (PREPOSICIONES - {"a"}):
            n += 1
        if sig == t and t in BORRABLES:
            n += 1
    return n


def bien_formada(tokens):
    return problemas(tokens) == 0


def correccion_basica(palabras):
    """Corrección sin modelo (respaldo si faltan los archivos del modelo):
    las mismas palabras del usuario, en su orden, con contracciones
    ("a el" -> "al"), mayúscula inicial y puntuación final."""
    tokens, pregunta, exclamacion = normalizar_entrada(palabras)
    if not tokens:
        return ""
    if len(tokens) == 1 and len(palabras) <= 1:
        return palabras[0].strip()
    tokens = [t if (i > 0 and t[:1].isupper() and not t.isupper()) else t.lower()
              for i, t in enumerate(tokens)]
    tipo = "pregunta" if (pregunta or tokens[0] in INTERROGATIVOS) else (
        "exclamacion" if exclamacion else "declarativa")
    return armar_texto(_conjunciones_eufonicas(_contracciones(tokens)), tipo)


# ── Corrector ─────────────────────────────────────────────────────────────────

class Corrector:
    MAX_PASADAS = 2

    def __init__(self, nlp, ruta_pesos, ruta_config, ruta_lexico):
        self.nlp = nlp
        with open(ruta_config, encoding="utf-8") as f:
            cfg = json.load(f)
        with open(ruta_lexico, encoding="utf-8") as f:
            self.lexico = json.load(f)
        self.inserciones = cfg["inserciones"]
        self.umbrales = cfg["umbrales"]
        self.vocab_palabras = {w: i for i, w in enumerate(cfg["vocab_palabras"])}
        self.vocab_sufijos = {s: i for i, s in enumerate(cfg["vocab_sufijos"])}
        self.red = RedEdiciones(np.load(ruta_pesos))
        self.indice = IndiceVerbal(self.lexico["verbos"])
        self.palabras_conocidas = set(self.lexico["palabras"])
        self.acentos = self.lexico["acentos"]
        self.acentos_seguros = self.lexico["acentos_seguros"]

    def es_palabra(self, w):
        return w in self.palabras_conocidas

    # ── Predicción de la red ─────────────────────────────────────────────────

    def _predecir(self, tokens):
        doc = doc_desde_palabras(self.nlp, tokens)
        palabras, sufijos = ids_doc(doc, self.vocab_palabras, self.vocab_sufijos)
        ins, tr, tipo = self.red(palabras, sufijos, vectores_doc(doc, self.nlp),
                                 rasgos_doc(doc, self.lexico, self.indice))
        return doc, ins, tr, tipo

    # ── Transformaciones (todas devuelven otra forma de la MISMA palabra) ────

    def _aplicar(self, etiqueta, token, doc_token, siguiente):
        t = token
        if etiqueta == "KEEP":
            return t
        if etiqueta.startswith("AGR_"):
            g, n = etiqueta[4], etiqueta[5]
            if t in DETERMINANTES:
                return flexionar_determinante(t, g, n, siguiente) or t
            if doc_token.pos_ in ("ADJ", "DET") or "Part" in doc_token.morph.get("VerbForm"):
                forma = flexionar_adjetivo(t, g, n, self.es_palabra)
                return forma if forma and self.es_palabra(forma) else t
            return t
        if etiqueta.startswith("V_"):
            tiempo = None
            tv = doc_token.morph.get("Tense")
            if "Sub" in doc_token.morph.get("Mood"):
                tiempo = "subj"
            elif "Cnd" in doc_token.morph.get("Mood"):
                tiempo = "cond"
            elif tv:
                tiempo = TIEMPO_SPACY.get(tv[0])
            return self.indice.cambiar_persona(t, etiqueta[2:], tiempo) or t
        if etiqueta == "ACC":
            if tiene_tilde(t):
                return t
            return self.acentos.get(t, t)
        if etiqueta == "DEL":
            return None if t in BORRABLES else t
        if etiqueta.startswith("REPL_"):
            return etiqueta[5:] if t in PREPOSICIONES_REEMPLAZABLES else t
        return t

    def _una_pasada(self, tokens, bloqueados):
        """Una pasada de la red: devuelve (tokens nuevos, bloqueados nuevos,
        tipo de frase, cantidad de ediciones)."""
        doc, ins, tr, tipo = self._predecir([t.lower() for t in tokens])
        th = self.umbrales
        ediciones = []   # (confianza, posición, tipo, valor)
        for i, t in enumerate(tokens):
            tl = t.lower()
            # 1) transformación: se suman las etiquetas que dan la misma forma
            if i not in bloqueados:
                siguiente = tokens[i + 1].lower() if i + 1 < len(tokens) else None
                por_forma = {}
                for j, etiqueta in enumerate(TRANSFORMACIONES):
                    forma = self._aplicar(etiqueta, tl, doc[i], siguiente)
                    clave = "<borrar>" if forma is None else forma
                    por_forma[clave] = por_forma.get(clave, 0.0) + float(tr[i, j])
                forma, prob = max(por_forma.items(), key=lambda x: x[1])
                if forma != tl:
                    umbral = th["borrar"] if forma == "<borrar>" else th["transformar"]
                    if prob >= umbral:
                        ediciones.append((prob, i, "tr", forma))
            # 2) inserción antes de la palabra i
            j = int(np.argmax(ins[i]))
            texto_ins = self.inserciones[j]
            if texto_ins != NADA and ins[i, j] >= th["insertar"]:
                if not (i == 0 and texto_ins.startswith(",")):
                    ediciones.append((float(ins[i, j]), i, "ins", texto_ins))

        # Tope de ediciones por pasada: las más seguras primero.
        tope = max(2, (len(tokens) + 1) // 2)
        ediciones.sort(key=lambda e: -e[0])
        ediciones = ediciones[:tope]

        aceptadas = []
        actual = problemas(tokens)
        for e in ediciones:
            candidato = self._construir(tokens, aceptadas + [e])[0]
            n = problemas(candidato)
            if n <= actual:
                aceptadas.append(e)
                actual = n
        nuevos, nuevos_bloqueados = self._construir(tokens, aceptadas, bloqueados)
        idx_tipo = int(np.argmax(tipo))
        tipo_frase = TIPOS_FRASE[idx_tipo] if tipo[idx_tipo] >= th["tipo"] else "declarativa"
        return nuevos, nuevos_bloqueados, tipo_frase, len(aceptadas)

    @staticmethod
    def _construir(tokens, ediciones, bloqueados=frozenset()):
        trans = {e[1]: e[3] for e in ediciones if e[2] == "tr"}
        inser = {e[1]: e[3] for e in ediciones if e[2] == "ins"}
        salida, bloq = [], set()
        for i, t in enumerate(tokens):
            if i in inser:
                for w in inser[i].replace(",", " , ").split():
                    bloq.add(len(salida))
                    salida.append(w)
            if i in trans:
                if trans[i] == "<borrar>":
                    continue
                forma = trans[i]
                if t[:1].isupper() and i > 0:
                    forma = forma[0].upper() + forma[1:]
                # "al" -> "a la" se separa en dos tokens para que problemas()
                # vea, por ejemplo, un "a la" insertado al lado ("a la a la").
                for w in forma.split():
                    bloq.add(len(salida))
                    salida.append(w)
            else:
                if i in bloqueados:
                    bloq.add(len(salida))
                salida.append(t)
        return salida, bloq

    # ── API ──────────────────────────────────────────────────────────────────

    def corregir(self, palabras):
        tokens, pregunta, exclamacion = normalizar_entrada(palabras)
        if not tokens:
            return ""
        if len(tokens) == 1 and len(palabras) <= 1:
            return palabras[0].strip() if isinstance(palabras[0], str) else ""
        # Minúsculas, salvo nombres propios (mayúscula fuera de la 1ª palabra).
        tokens = [t if (i > 0 and t[:1].isupper() and not t.isupper()) else t.lower()
                  for i, t in enumerate(tokens)]
        # Tildes que no tienen ambigüedad ("despues" -> "después").
        tokens = [self.acentos_seguros.get(t, t) for t in tokens]
        original = list(tokens)
        tipo = "declarativa"
        bloqueados = set()
        try:
            for pasada in range(self.MAX_PASADAS):
                tokens, bloqueados, tipo_pasada, cambios = self._una_pasada(tokens, bloqueados)
                if pasada == 0:
                    tipo = tipo_pasada
                if not cambios:
                    break
        except Exception:      # nunca dejar al usuario sin respuesta
            tokens = original
        if problemas(tokens) > problemas(original):
            tokens = original
        if pregunta or tokens[0].lower() in INTERROGATIVOS:
            tipo = "pregunta"
        elif exclamacion:
            tipo = "exclamacion"
        tokens = _conjunciones_eufonicas(_contracciones(tokens))
        return armar_texto(tokens, tipo)
