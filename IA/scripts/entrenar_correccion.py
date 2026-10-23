"""
Entrena el corrector de frases (/corregir) y genera los archivos que usa
correccion.py en producción:
  IA/modelo_correccion.npz      pesos de la red (numpy)
  IA/modelo_correccion.json     vocabularios, etiquetas de inserción y umbrales
  IA/lexico_correccion.json     léxico: género de sustantivos, tildes, verbos

Datos: frases CORRECTAS de
  - scripts/datos/corpus_caa.txt      frases de CAA generadas (corpus_caa.py)
  - scripts/datos/frases_curadas.txt  frases escritas a mano
  - scripts/datos/externos/tatoeba_es.txt  (OPCIONAL) muestra de oraciones
    reales de Tatoeba (descargar_tatoeba.py), para variedad de estructuras.
    Si no está (p. ej. en una red que bloquea la descarga) se entrena solo con
    las dos primeras, generando más roturas distintas de cada frase.
Cada frase se "rompe" a propósito con los errores típicos de un usuario que
arma la frase palabra por palabra, y la red aprende a deshacerlos:
  - falta un artículo, preposición, contracción, "que", "y", "me" o una coma
  - artículo/adjetivo con género o número equivocado ("la perro")
  - verbo en otra persona que su sujeto ("yo quiere") - solo si el sujeto
    está explícito, si no la frase original también podría ser válida
  - falta una tilde ("mama", "esta cansado")
  - sobra una palabra funcional ("la mi casa") o se cambió una preposición
Como las roturas las hacemos nosotros, la etiqueta correcta de cada palabra
se conoce exactamente (no hace falta alinear frases).

Uso (desde IA/):  python scripts/entrenar_correccion.py
(--rehacer para regenerar el dataset en caché, p. ej. después de descargar Tatoeba)
Requiere torch (solo para entrenar): pip install -r scripts/requirements-entrenamiento.txt
"""

import json
import os
import pickle
import random
import re
import sys
import time
from collections import Counter, defaultdict

import numpy as np
from spacy.tokens import Doc

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from correccion import (  # noqa: E402
    BORRABLES, DIM_RASGOS, NADA, PIPES_RASGOS, PREPOSICIONES_REEMPLAZABLES, TIPOS_FRASE,
    TRANSFORMACIONES, ids_doc, rasgos_doc, sufijo,
)
from morfologia import (  # noqa: E402
    DETERMINANTES, FEMENINAS_A_TONICA, PERSONAS, IndiceVerbal, base_adjetivo, es_infinitivo,
    flexionar_determinante, formas_adjetivo, paradigma, quitar_tildes, rasgos_adjetivo,
    rasgos_determinante, tiene_tilde,
)

SEMILLA = 13
N_TATOEBA = 90000
# Roturas distintas que se generan de cada frase de entrenamiento. Sin Tatoeba
# hay ~3 veces menos frases: se generan más por frase para llegar a una
# cantidad de ejemplos parecida.
VARIANTES = {"caa": 2, "curadas": 3, "tatoeba": 1}
VARIANTES_SIN_TATOEBA = {"caa": 4, "curadas": 6}
N_VAL = 6000
# Versión rápida (~10 min en vez de ~75): una sola rotura por frase y como
# mucho MAX_EJEMPLOS ejemplos de entrenamiento. None = dataset completo.
# El léxico se arma igual con todas las frases.
MAX_EJEMPLOS = 10000
N_VAL_RAPIDO = 1000
DATOS = os.path.join(AQUI, "datos")
CACHE = os.path.join(DATOS, "cache")
FUENTES = {
    "caa": os.path.join(DATOS, "corpus_caa.txt"),
    "curadas": os.path.join(DATOS, "frases_curadas.txt"),
    "tatoeba": os.path.join(DATOS, "externos", "tatoeba_es.txt"),
}
SALIDA_PESOS = os.path.join(RAIZ, "modelo_correccion.npz")
SALIDA_CONFIG = os.path.join(RAIZ, "modelo_correccion.json")
SALIDA_LEXICO = os.path.join(RAIZ, "lexico_correccion.json")

MAX_VOCAB = 9000
MAX_SUFIJOS = 2500
MIN_FREC_INSERCION = 25
MAX_INSERCIONES = 150

# Tildes diacríticas en desuso (RAE 2010) que todavía aparecen en Tatoeba.
_NORMALIZAR = {"sólo": "solo", "éste": "este", "ésta": "esta", "éstos": "estos", "éstas": "estas",
               "ése": "ese", "ésa": "esa", "ésos": "esos", "ésas": "esas", "aquél": "aquel",
               "aquélla": "aquella", "fué": "fue", "dió": "dio", "vió": "vio", "guión": "guion",
               "tí": "ti", "fuí": "fui", "Sólo": "Solo", "Éste": "Este", "Ésta": "Esta", "Ése": "Ese",
               "Ésa": "Esa"}
_TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^\w\s]")

ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
PREPS_BORRABLES = {"a", "de", "en", "con", "para", "por"}
CONFUSION_PREP = {"a": ["en", "para"], "en": ["a", "de"], "de": ["con", "en"], "con": ["de", "a"],
                  "para": ["por", "a"], "por": ["para", "de"]}
CONFUSION_PERSONA = {"1s": ["3s", "3s", "1p", "2v"], "2s": ["3s", "1s"], "2v": ["3s", "1s"],
                     "3s": ["1s", "3p", "3p", "2v"], "1p": ["3p", "1s", "3s"], "3p": ["3s", "3s", "1p"]}
ESPURIAS = ["el", "la", "un", "los", "las", "una"]
ANTES_DE_ESPURIA = {"mi", "mis", "tu", "tus", "su", "sus", "el", "la", "los", "las", "este", "esta",
                    "estos", "estas", "ese", "esa", "un", "una"}


# ── Lectura ───────────────────────────────────────────────────────────────────

def leer(fuente):
    with open(FUENTES[fuente], encoding="utf-8") as f:
        frases = [l.strip() for l in f if l.strip()]
    if fuente == "tatoeba":
        random.Random(SEMILLA).shuffle(frases)
        frases = frases[:N_TATOEBA]
    return frases


def tokenizar_limpia(frase):
    """Frase correcta -> (palabras en minúscula + comas, tipo de frase)."""
    toks = [_NORMALIZAR.get(t, t) for t in _TOKEN.findall(frase)]
    tipo = "pregunta" if "?" in toks else ("exclamacion" if "!" in toks else "declarativa")
    salida = []
    for t in toks:
        if t == ",":
            if salida and salida[-1] != ",":
                salida.append(",")
        elif t[0].isalpha():
            salida.append(t.lower())
    while salida and salida[-1] == ",":
        salida.pop()
    if not salida or salida[0] == ",":
        return None, None
    return salida, tipo


# ── Léxico ────────────────────────────────────────────────────────────────────

def construir_lexico(docs, vocab):
    frec = Counter()
    votos_genero = defaultdict(Counter)
    infinitivos = Counter()
    lemas = Counter()
    for doc in docs:
        for i, t in enumerate(doc):
            w = t.text
            if not w.isalpha():
                continue
            frec[w] += 1
            if t.pos_ == "NOUN":
                g = t.morph.get("Gender")
                if g:
                    votos_genero[w]["f" if g[0] == "Fem" else "m"] += 1
                if i > 0 and doc[i - 1].text in DETERMINANTES:
                    r = rasgos_determinante(doc[i - 1].text)
                    if r and r[0]:
                        gd = r[0]
                        if gd == "m" and r[1] == "s" and w in FEMENINAS_A_TONICA:
                            gd = "f"
                        votos_genero[w][gd] += 2
            if "Inf" in t.morph.get("VerbForm") and es_infinitivo(w) and t.pos_ in ("VERB", "AUX"):
                infinitivos[w] += 1
            # Verbos que solo aparecen conjugados ("quiero", "tengo"): se usa
            # el lema de spaCy, que a veces inventa lemas ("querrir"); solo se
            # acepta si es una palabra real (tiene vector) y genera la forma.
            l = t.lemma_.lower()
            if "Fin" in t.morph.get("VerbForm") and t.pos_ in ("VERB", "AUX") and es_infinitivo(l) \
                    and vocab.has_vector(l) and w in {f for fs in paradigma(l).values() for f in fs}:
                lemas[l] += 1
    genero = {}
    for w, votos in votos_genero.items():
        total = sum(votos.values())
        g, c = votos.most_common(1)[0]
        if total >= 2 and c / total >= 0.8:
            genero[w] = g
    for w in FEMENINAS_A_TONICA:
        genero[w] = "f"
    verbos = sorted({w for w, c in infinitivos.items() if c >= 2} | {l for l, c in lemas.items() if c >= 2})
    indice = IndiceVerbal(verbos)
    formas_verbales = set(indice.formas())

    acentos, acentos_seguros = {}, {}
    por_clave = defaultdict(list)
    for w, c in frec.items():
        if tiene_tilde(w):
            por_clave[quitar_tildes(w)].append((c, w))
    for clave, lista in por_clave.items():
        c, w = max(lista)
        acentos[clave] = w
        if frec.get(clave, 0) == 0 and c >= 3 and clave not in formas_verbales and len(lista) == 1:
            acentos_seguros[clave] = w
    palabras = sorted({w for w, c in frec.items() if c >= 2} | formas_verbales)
    return {
        "genero": genero, "acentos": acentos, "acentos_seguros": acentos_seguros,
        "verbos": verbos, "palabras": palabras,
    }, frec


# ── Corrupción ────────────────────────────────────────────────────────────────

def persona_spacy(t, indice):
    """Persona de un verbo conjugado según spaCy + el índice verbal."""
    per = t.morph.get("Person")
    num = t.morph.get("Number")
    if not per or not num:
        return None
    clave = {("1", "Sing"): "1s", ("2", "Sing"): "2s", ("3", "Sing"): "3s",
             ("1", "Plur"): "1p", ("3", "Plur"): "3p", ("2", "Plur"): "3p"}.get((per[0], num[0]))
    if clave is None:
        return None
    analisis = indice.analizar(t.text)
    personas = {a[2] for a in analisis}
    if clave == "2s" and "2v" in personas and "2s" not in personas:
        clave = "2v"
    return clave if clave in personas else None


def tiene_sujeto(t):
    if any(h.dep_.startswith("nsubj") for h in t.children):
        return True
    if t.dep_ in ("cop", "aux") and any(h.dep_.startswith("nsubj") for h in t.head.children):
        return True
    return False


def genero_cabeza(t, lexico):
    cabeza = t.head
    g = lexico["genero"].get(cabeza.text)
    if g:
        return g
    morf = cabeza.morph.get("Gender")
    if morf:
        return "f" if morf[0] == "Fem" else "m"
    return "m"


def corromper(doc, tipo, rng, lexico, indice):
    """Frase limpia (Doc con comas) -> (palabras de entrada, etiqueta de
    inserción por palabra, etiqueta de transformación por palabra, tipo)."""
    n = len(doc)
    accion = [None] * n      # None | "del" | ("tr", forma_corrupta, etiqueta)
    for i, t in enumerate(doc):
        if t.text == ",":
            accion[i] = "del"
    palabras_idx = [i for i in range(n) if doc[i].text != ","]
    if len(palabras_idx) < 2:
        return None

    def ultimo_palabra(i):
        return i == palabras_idx[-1]

    # 1) Borrar palabras funcionales (el usuario no las puso).
    candidatos = []
    for i in palabras_idx:
        t = doc[i]
        w = t.text
        if ultimo_palabra(i):
            continue
        if w in ARTICULOS and t.pos_ == "DET":
            candidatos.append(i)
        elif w in ("al", "del") or (w in PREPS_BORRABLES and t.pos_ == "ADP"):
            candidatos.append(i)
        elif w == "que" and t.pos_ == "SCONJ" and rng.random() < 0.6:
            candidatos.append(i)
        elif w == "y" and t.pos_ == "CCONJ" and rng.random() < 0.4:
            candidatos.append(i)
        elif w == "me" and i + 1 < n and doc[i + 1].pos_ in ("VERB", "AUX") and rng.random() < 0.5:
            candidatos.append(i)
    k = rng.choices([0, 1, 2, 3], [0.28, 0.36, 0.23, 0.13])[0]
    rng.shuffle(candidatos)
    for i in candidatos[:k]:
        accion[i] = "del"
        if doc[i].text in PREPS_BORRABLES and i + 1 < n and doc[i + 1].text in ARTICULOS | {"mi", "mis"} \
                and not ultimo_palabra(i + 1) and rng.random() < 0.5:
            accion[i + 1] = "del"

    # "a la plaza" -> "al plaza": contracción con el género/número equivocado.
    if rng.random() < 0.05:
        for i in rng.sample(palabras_idx, len(palabras_idx)):
            if accion[i] is None and doc[i].text in ("a", "de") and i + 2 < n \
                    and doc[i + 1].text in ("la", "los", "las") and accion[i + 1] is None \
                    and doc[i + 2].text not in FEMENINAS_A_TONICA:
                g, nn = rasgos_determinante(doc[i + 1].text)
                accion[i] = ("tr", doc[i].text + "l", f"AGR_{g}{nn}")
                accion[i + 1] = "quitar"
                break

    libres = [i for i in palabras_idx if accion[i] is None]

    # 2) Concordancia de género / número.
    if rng.random() < 0.38:
        cands = []
        for i in libres:
            t = doc[i]
            if t.text in DETERMINANTES and t.pos_ in ("DET", "ADP"):
                cands.append(i)
            elif t.pos_ == "ADJ" or ("Part" in t.morph.get("VerbForm") and t.pos_ in ("ADJ", "VERB")):
                cands.append(i)
        rng.shuffle(cands)
        for i in cands[: rng.choice([1, 1, 1, 2])]:
            t = doc[i]
            w = t.text
            sig = doc[i + 1].text if i + 1 < n else None
            if w in DETERMINANTES:
                g, nn = rasgos_determinante(w)
                if g is None:
                    g = genero_cabeza(t, lexico)
                if w in ("al", "del"):
                    g, nn = "m", "s"
                opciones = [(gg, x) for gg in "mf" for x in "sp" if (gg, x) != (g, nn)]
                rng.shuffle(opciones)
                for gg, x in opciones:
                    forma = flexionar_determinante(w, gg, x, sig)
                    if forma and forma != w and " " not in forma:
                        accion[i] = ("tr", forma, f"AGR_{g}{nn}")
                        break
            else:
                base = base_adjetivo(w, lambda p: p in lexico["palabras_set"])
                formas = formas_adjetivo(base)
                if w not in formas.values():
                    continue
                g, nn = rasgos_adjetivo(w)
                if g is None:
                    g = genero_cabeza(t, lexico)
                if formas.get((g, nn)) != w:
                    continue
                distintas = [(k2, f) for k2, f in formas.items() if f != w]
                if distintas:
                    _, forma = rng.choice(distintas)
                    accion[i] = ("tr", forma, f"AGR_{g}{nn}")

    # 3) Persona del verbo (solo con sujeto explícito).
    if rng.random() < 0.22:
        for i in rng.sample(libres, len(libres)):
            t = doc[i]
            if accion[i] is not None or "Fin" not in t.morph.get("VerbForm") or not tiene_sujeto(t):
                continue
            per = persona_spacy(t, indice)
            if per is None:
                continue
            tiempo = None
            for v, tv, pv in indice.analizar(t.text):
                if pv == per:
                    tiempo = tv
                    break
            nueva = rng.choice(CONFUSION_PERSONA[per])
            forma = indice.cambiar_persona(t.text, nueva, tiempo)
            if forma and forma != t.text:
                accion[i] = ("tr", forma, f"V_{per}")
                break

    # 4) Tildes.
    r = rng.random()
    con_tilde = [i for i in palabras_idx if accion[i] is None and tiene_tilde(doc[i].text)
                 and lexico["acentos"].get(quitar_tildes(doc[i].text)) == doc[i].text]
    if r < 0.08:
        elegidas = con_tilde
    elif r < 0.33:
        rng.shuffle(con_tilde)
        elegidas = con_tilde[: rng.choice([1, 1, 2])]
    else:
        elegidas = []
    for i in elegidas:
        accion[i] = ("tr", quitar_tildes(doc[i].text), "ACC")

    # 5) Cambiar una preposición.
    if rng.random() < 0.06:
        cands = [i for i in palabras_idx if accion[i] is None and doc[i].text in CONFUSION_PREP
                 and doc[i].pos_ == "ADP"]
        if cands:
            i = rng.choice(cands)
            accion[i] = ("tr", rng.choice(CONFUSION_PREP[doc[i].text]), f"REPL_{doc[i].text}")

    # Armar entrada y etiquetas.
    entrada, ins, tr = [], [], []
    pendiente = []
    for i, t in enumerate(doc):
        a = accion[i]
        if a == "quitar":
            continue
        if a == "del":
            pendiente.append(t.text)
            continue
        ins.append(" ".join(pendiente).replace(" ,", ",") if pendiente else NADA)
        pendiente = []
        if a is None:
            entrada.append(t.text)
            tr.append("KEEP")
        else:
            entrada.append(a[1])
            tr.append(a[2])
    if pendiente or len(entrada) < 2:
        return None

    # 6) Palabra funcional de más (se debe borrar). Solo donde seguro sobra:
    # artículo delante de otro determinante ("la mi casa") o una palabra
    # funcional repetida ("de de").
    if rng.random() < 0.07:
        r = rng.random()
        if r < 0.3:
            pos = [p for p in range(len(entrada) - 1) if entrada[p] in BORRABLES and tr[p] == "KEEP"]
            if pos:
                p = rng.choice(pos)
                entrada.insert(p + 1, entrada[p])
                ins.insert(p + 1, NADA)
                tr.insert(p + 1, "DEL")
        else:
            pos = [p for p in range(len(entrada)) if entrada[p] in ANTES_DE_ESPURIA and tr[p] == "KEEP"
                   and ins[p] == NADA]
            if pos:
                p = rng.choice(pos)
                entrada.insert(p, rng.choice(ESPURIAS))
                ins.insert(p, NADA)
                tr.insert(p, "DEL")
    return entrada, ins, tr, tipo


# ── Preparación del dataset ───────────────────────────────────────────────────

def preparar():
    import spacy

    rng = random.Random(SEMILLA)
    print("Cargando spaCy...")
    nlp = spacy.load("es_core_news_md")

    if os.path.exists(FUENTES["tatoeba"]):
        variantes = VARIANTES
    else:
        print(f"No está {FUENTES['tatoeba']}: se entrena solo con corpus_caa y frases_curadas")
        variantes = VARIANTES_SIN_TATOEBA

    frases = []
    for fuente in variantes:
        lista = leer(fuente)
        print(f"{fuente}: {len(lista)} frases")
        for f in lista:
            toks, tipo = tokenizar_limpia(f)
            if toks and len(toks) >= 2:
                frases.append((fuente, toks, tipo))
    # División por frase: las de validación nunca se ven al entrenar.
    rng.shuffle(frases)
    n_val = min(N_VAL if MAX_EJEMPLOS is None else N_VAL_RAPIDO, len(frases) // 10)
    val_ids = set(range(n_val))

    print(f"Analizando {len(frases)} frases limpias con spaCy...")
    t0 = time.time()
    docs_limpios = list(nlp.pipe((Doc(nlp.vocab, words=t) for _, t, _ in frases),
                                 batch_size=512, disable=["ner"]))
    print(f"  {time.time() - t0:.0f}s")

    lexico, frec = construir_lexico(docs_limpios, nlp.vocab)
    lexico["palabras_set"] = set(lexico["palabras"])
    indice = IndiceVerbal(lexico["verbos"])
    print(f"Léxico: {len(lexico['genero'])} géneros, {len(lexico['acentos'])} tildes "
          f"({len(lexico['acentos_seguros'])} seguras), {len(lexico['verbos'])} verbos, "
          f"{len(lexico['palabras'])} palabras")

    ejemplos = []   # (es_val, entrada, ins, tr, tipo)
    n_train = 0
    for k, ((fuente, toks, tipo), doc) in enumerate(zip(frases, docs_limpios)):
        es_val = k in val_ids
        if not es_val and MAX_EJEMPLOS is not None and n_train >= MAX_EJEMPLOS:
            break
        for _ in range(1 if es_val or MAX_EJEMPLOS is not None else variantes[fuente]):
            r = corromper(doc, tipo, rng, lexico, indice)
            if r:
                ejemplos.append((es_val,) + r)
                n_train += not es_val
    print(f"Ejemplos corruptos: {len(ejemplos)}")

    print("Calculando rasgos de las entradas corruptas...")
    t0 = time.time()
    with nlp.select_pipes(enable=PIPES_RASGOS):
        docs = list(nlp.pipe((Doc(nlp.vocab, words=e[1]) for e in ejemplos), batch_size=512))
    print(f"  {time.time() - t0:.0f}s")

    frec_palabras = Counter(w for e in ejemplos if not e[0] for w in e[1])
    frec_sufijos = Counter(sufijo(w) for e in ejemplos if not e[0] for w in e[1])
    vocab_palabras = ["<pad>", "<unk>"] + [w for w, _ in frec_palabras.most_common(MAX_VOCAB)]
    vocab_sufijos = ["<pad>", "<unk>"] + [s for s, _ in frec_sufijos.most_common(MAX_SUFIJOS)]
    frec_ins = Counter(x for e in ejemplos if not e[0] for x in e[2] if x != NADA)
    min_frec = MIN_FREC_INSERCION if MAX_EJEMPLOS is None else 10
    inserciones = [NADA] + [x for x, c in frec_ins.most_common(MAX_INSERCIONES) if c >= min_frec]
    print(f"Etiquetas de inserción: {len(inserciones)} (más comunes: {inserciones[1:16]})")
    vp = {w: i for i, w in enumerate(vocab_palabras)}
    vs = {s: i for i, s in enumerate(vocab_sufijos)}
    ii = {x: i for i, x in enumerate(inserciones)}
    ti = {x: i for i, x in enumerate(TRANSFORMACIONES)}

    tabla = nlp.vocab.vectors
    datos = []
    for e, doc in zip(ejemplos, docs):
        es_val, entrada, ins, tr, tipo = e
        palabras, sufijos = ids_doc(doc, vp, vs)
        filas = np.array([tabla.key2row.get(nlp.vocab.strings[w], -1) for w in entrada], dtype=np.int32)
        rasgos = rasgos_doc(doc, lexico, indice).astype(np.uint8)
        y_ins = np.array([ii.get(x, 0) for x in ins], dtype=np.int64)
        y_tr = np.array([ti[x] for x in tr], dtype=np.int64)
        datos.append((es_val, palabras, sufijos, filas, rasgos, y_ins, y_tr, TIPOS_FRASE.index(tipo), entrada, ins, tr))
    del lexico["palabras_set"]
    meta = {"vocab_palabras": vocab_palabras, "vocab_sufijos": vocab_sufijos, "inserciones": inserciones}
    vectores = np.array(tabla.data, dtype=np.float32)
    return datos, meta, lexico, vectores


# ── Modelo ────────────────────────────────────────────────────────────────────

def entrenar(datos, meta, vectores):
    import torch
    import torch.nn as nn

    torch.manual_seed(SEMILLA)
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 2))

    class ModeloEdiciones(nn.Module):
        def __init__(self, n_pal, n_suf, dim_vec, n_ins, n_tr, n_tipo, emb=64, emb_suf=24, proy=64,
                     hidden=160, capas=2, dropout=0.25):
            super().__init__()
            self.emb_palabra = nn.Embedding(n_pal, emb, padding_idx=0)
            self.emb_sufijo = nn.Embedding(n_suf, emb_suf, padding_idx=0)
            self.proy_vector = nn.Linear(dim_vec, proy, bias=False)
            self.entrada = nn.Linear(emb + emb_suf + proy + DIM_RASGOS, hidden)
            self.gru = nn.GRU(hidden, hidden, num_layers=capas, bidirectional=True, batch_first=True,
                              dropout=dropout)
            self.cabeza_ins = nn.Linear(2 * hidden, n_ins)
            self.cabeza_tr = nn.Linear(2 * hidden, n_tr)
            self.cabeza_tipo = nn.Linear(4 * hidden, n_tipo)
            self.drop = nn.Dropout(dropout)

        def forward(self, pal, suf, vec, ras, largos):
            x = torch.cat([self.emb_palabra(pal), self.emb_sufijo(suf), self.proy_vector(vec), ras], dim=2)
            x = torch.tanh(self.entrada(self.drop(x)))
            empaq = nn.utils.rnn.pack_padded_sequence(x, largos.cpu(), batch_first=True, enforce_sorted=False)
            salida, _ = self.gru(empaq)
            salida, _ = nn.utils.rnn.pad_packed_sequence(salida, batch_first=True, total_length=pal.size(1))
            h = self.drop(salida)
            mascara = (pal != 0).unsqueeze(2).float()
            media = (salida * mascara).sum(1) / mascara.sum(1)
            maximo = salida.masked_fill(mascara == 0, -1e9).max(1).values
            return self.cabeza_ins(h), self.cabeza_tr(h), self.cabeza_tipo(torch.cat([media, maximo], 1))

    vec_t = torch.tensor(np.vstack([vectores, np.zeros((1, vectores.shape[1]), dtype=np.float32)]))
    fila_cero = vectores.shape[0]

    def lote(muestras, dropout_palabra=0.0):
        L = max(len(m[1]) for m in muestras)
        B = len(muestras)
        pal = torch.zeros(B, L, dtype=torch.long)
        suf = torch.zeros(B, L, dtype=torch.long)
        filas = torch.full((B, L), fila_cero, dtype=torch.long)
        ras = torch.zeros(B, L, DIM_RASGOS)
        yi = torch.full((B, L), -100, dtype=torch.long)
        yt = torch.full((B, L), -100, dtype=torch.long)
        tipo = torch.zeros(B, dtype=torch.long)
        largos = torch.zeros(B, dtype=torch.long)
        for b, m in enumerate(muestras):
            n = len(m[1])
            p = torch.from_numpy(m[1])
            if dropout_palabra:
                p = torch.where(torch.rand(n) < dropout_palabra, torch.ones_like(p), p)
            pal[b, :n] = p
            suf[b, :n] = torch.from_numpy(m[2])
            f = torch.from_numpy(m[3].astype(np.int64))
            filas[b, :n] = torch.where(f < 0, torch.full_like(f, fila_cero), f)
            ras[b, :n] = torch.from_numpy(m[4].astype(np.float32))
            yi[b, :n] = torch.from_numpy(m[5])
            yt[b, :n] = torch.from_numpy(m[6])
            tipo[b] = m[7]
            largos[b] = n
        return pal, suf, vec_t[filas], ras, largos, yi, yt, tipo

    train = [d for d in datos if not d[0]]
    val = [d for d in datos if d[0]]
    print(f"Train: {len(train)} | Val: {len(val)}")
    modelo = ModeloEdiciones(len(meta["vocab_palabras"]), len(meta["vocab_sufijos"]), vectores.shape[1],
                             len(meta["inserciones"]), len(TRANSFORMACIONES), len(TIPOS_FRASE))
    print(f"Parámetros: {sum(p.numel() for p in modelo.parameters()):,}")
    opt = torch.optim.Adam(modelo.parameters(), lr=2e-3)
    ce = nn.CrossEntropyLoss(ignore_index=-100)
    EPOCHS, BATCH = (9 if MAX_EJEMPLOS is None else 12), 128
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=EPOCHS * (len(train) // BATCH + 1))

    def evaluar():
        modelo.eval()
        preds = []
        with torch.no_grad():
            for i in range(0, len(val), 512):
                m = val[i:i + 512]
                pal, suf, vec, ras, largos, yi, yt, tipo = lote(m)
                oi, ot, otp = modelo(pal, suf, vec, ras, largos)
                pi, pt, ptp = oi.softmax(-1), ot.softmax(-1), otp.softmax(-1)
                for b in range(len(m)):
                    n = len(m[b][1])
                    preds.append((pi[b, :n].numpy(), pt[b, :n].numpy(), ptp[b].numpy()))
        modelo.train()
        return preds

    mejor = None
    for epoch in range(1, EPOCHS + 1):
        random.Random(epoch).shuffle(train)
        # lotes de largo parecido (más rápido) en orden aleatorio
        orden = sorted(range(len(train)), key=lambda i: (len(train[i][1]), random.random()))
        lotes = [orden[i:i + BATCH] for i in range(0, len(orden), BATCH)]
        random.Random(epoch + 100).shuffle(lotes)
        t0, total = time.time(), 0.0
        for paso, ids in enumerate(lotes):
            pal, suf, vec, ras, largos, yi, yt, tipo = lote([train[i] for i in ids], dropout_palabra=0.08)
            oi, ot, otp = modelo(pal, suf, vec, ras, largos)
            loss = ce(oi.reshape(-1, oi.size(-1)), yi.reshape(-1)) + \
                ce(ot.reshape(-1, ot.size(-1)), yt.reshape(-1)) + 0.3 * ce(otp, tipo)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            opt.step()
            sched.step()
            total += loss.item()
        preds = evaluar()
        m = metricas(val, preds, meta, {"insertar": 0.5, "transformar": 0.5, "borrar": 0.5, "tipo": 0.5})
        print(f"Epoch {epoch} | loss {total / len(lotes):.4f} | {time.time() - t0:.0f}s | "
              f"ins P={m['ins_p']:.3f} R={m['ins_r']:.3f} | tr P={m['tr_p']:.3f} R={m['tr_r']:.3f} | "
              f"frases exactas {m['exactas']:.3f} | tipo {m['tipo']:.3f}", flush=True)
        mejor = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
    modelo.load_state_dict(mejor)
    return modelo, evaluar()


def metricas(val, preds, meta, umbrales):
    """Precisión / recall de las ediciones (a nivel etiqueta) y % de frases
    del set de validación que quedan exactamente bien."""
    vp = tp = fp = fn = 0
    tvp = tfp = tfn = 0
    exactas = 0
    tipo_ok = 0
    for d, (pi, pt, ptp) in zip(val, preds):
        y_ins, y_tr = d[5], d[6]
        ok = True
        for i in range(len(y_ins)):
            j = int(pi[i].argmax())
            pred_ins = j if (j != 0 and pi[i, j] >= umbrales["insertar"]) else 0
            if pred_ins != 0 and pred_ins == y_ins[i]:
                tp += 1
            elif pred_ins != 0:
                fp += 1
                ok = False
            if y_ins[i] != 0 and pred_ins != y_ins[i]:
                fn += 1
                ok = False
            k = int(pt[i].argmax())
            u = umbrales["borrar"] if TRANSFORMACIONES[k] == "DEL" else umbrales["transformar"]
            pred_tr = k if (k != 0 and pt[i, k] >= u) else 0
            if pred_tr != 0 and pred_tr == y_tr[i]:
                tvp += 1
            elif pred_tr != 0:
                tfp += 1
                ok = False
            if y_tr[i] != 0 and pred_tr != y_tr[i]:
                tfn += 1
                ok = False
        exactas += ok
        t = int(ptp.argmax())
        t = t if ptp[t] >= umbrales["tipo"] else 0
        tipo_ok += (t == d[7])
    n = max(len(val), 1)
    return {
        "ins_p": tp / max(tp + fp, 1), "ins_r": tp / max(tp + fn, 1),
        "tr_p": tvp / max(tvp + tfp, 1), "tr_r": tvp / max(tvp + tfn, 1),
        "exactas": exactas / n, "tipo": tipo_ok / n,
    }


def elegir_umbrales(val, preds, meta):
    """Umbrales lo más bajos posible manteniendo precisión >= 0.97 en
    inserciones y transformaciones (preferimos no corregir a corregir mal)."""
    mejores = {}
    for familia, clave_p in (("insertar", "ins_p"), ("transformar", "tr_p")):
        elegido = 0.9
        for u in [x / 100 for x in range(40, 96, 5)]:
            base = {"insertar": 0.5, "transformar": 0.5, "borrar": 0.9, "tipo": 0.6}
            base[familia] = u
            m = metricas(val, preds, meta, base)
            if m[clave_p] >= 0.97:
                elegido = u
                break
        mejores[familia] = elegido
    mejores["borrar"] = max(0.85, mejores["transformar"])
    mejores["tipo"] = 0.7
    m = metricas(val, preds, meta, mejores)
    print(f"Umbrales: {mejores} -> ins P={m['ins_p']:.3f} R={m['ins_r']:.3f} | "
          f"tr P={m['tr_p']:.3f} R={m['tr_r']:.3f} | exactas {m['exactas']:.3f}")
    return mejores


def exportar(modelo, meta, lexico, umbrales):
    pesos = {k: v.detach().cpu().numpy().astype(np.float32) for k, v in modelo.state_dict().items()}
    np.savez_compressed(SALIDA_PESOS, **pesos)
    with open(SALIDA_CONFIG, "w", encoding="utf-8") as f:
        json.dump({**meta, "umbrales": umbrales, "transformaciones": TRANSFORMACIONES,
                   "tipos_frase": TIPOS_FRASE}, f, ensure_ascii=False)
    with open(SALIDA_LEXICO, "w", encoding="utf-8") as f:
        json.dump(lexico, f, ensure_ascii=False)
    for ruta in (SALIDA_PESOS, SALIDA_CONFIG, SALIDA_LEXICO):
        print(f"Guardado {ruta} ({os.path.getsize(ruta) // 1024} KB)")


def main():
    os.makedirs(CACHE, exist_ok=True)
    ruta_cache = os.path.join(CACHE, "dataset_correccion.pkl")
    if os.path.exists(ruta_cache) and "--rehacer" not in sys.argv:
        print(f"Usando dataset en caché ({ruta_cache}); --rehacer para regenerarlo")
        with open(ruta_cache, "rb") as f:
            datos, meta, lexico, vectores = pickle.load(f)
    else:
        datos, meta, lexico, vectores = preparar()
        with open(ruta_cache, "wb") as f:
            pickle.dump((datos, meta, lexico, vectores), f, protocol=pickle.HIGHEST_PROTOCOL)
    if "--solo-datos" in sys.argv:
        random.seed(1)
        for d in random.sample(datos, 40):
            pares = []
            for w, a, b in zip(d[8], d[9], d[10]):
                pares.append((f"[{a}] " if a else "") + w + (f"<{b}>" if b != "KEEP" else ""))
            print(" ".join(pares), "|", TIPOS_FRASE[d[7]])
        return
    modelo, preds = entrenar(datos, meta, vectores)
    val = [d for d in datos if d[0]]
    umbrales = elegir_umbrales(val, preds, meta)
    exportar(modelo, meta, lexico, umbrales)


if __name__ == "__main__":
    main()
