"""
Conjugación y armado de cláusulas simples por reglas.

El modelo seq2seq (modelo_correccion.py) solo puede escribir palabras que vio
al entrenar, así que no puede conjugar "dormir" -> "dormí" si esa forma no
estaba en el dataset. Este módulo cubre ese hueco sin inventar contenido: toma
el verbo que el usuario eligió y lo pasa a otra forma de la MISMA palabra
(primera persona, presente o pretérito), y arma la cláusula en orden natural
(negación + verbo + complementos con su preposición y artículo).

Se usa como respaldo cuando el modelo no logra una frase que conjugue el verbo.
"""

import re

from gramatica import lema, FUNCIONALES, OMITIBLES

_INFINITIVO = re.compile(r"^[a-záéíóúüñ]*(ar|er|ir|ír)$")

# ── Cache de POS por palabra suelta ──────────────────────────────────────────

_cache_pos = {}


def _pos(nlp, palabra):
    clave = palabra.lower()
    if clave not in _cache_pos:
        doc = nlp(clave)
        _cache_pos[clave] = doc[0].pos_ if len(doc) else ""
    return _cache_pos[clave]


def es_verbo(nlp, palabra):
    return _pos(nlp, palabra) in ("VERB", "AUX")


def es_infinitivo(nlp, palabra):
    """True si `palabra` es un verbo en infinitivo (sin clíticos: "cambiarme"
    no cuenta) que sabemos conjugar."""
    p = palabra.lower()
    if not _INFINITIVO.match(p) or lema(nlp, p) != p:
        return False
    # spaCy etiqueta como sustantivo algunos infinitivos sueltos ("poder"):
    # las tablas de verbos conocidos los rescatan.
    return es_verbo(nlp, p) or p in _PRES_IRREG or p in _PRES_RAIZ or p in ESTATIVOS


GOBERNADORES = {   # verbos que rigen un infinitivo: "quiero comer", "voy a comer"
    "querer", "poder", "necesitar", "deber", "soler", "saber", "intentar", "ir",
    "empezar", "comenzar", "tratar", "dejar", "seguir", "gustar", "preferir",
    "odiar", "amar", "tener", "haber", "pensar", "esperar", "lograr", "decidir",
    "prometer", "volver", "acabar", "terminar", "ayudar", "permitir", "prohibir",
}
PREPOSICIONES_INF = {"a", "de", "para", "por", "sin", "al", "del", "con", "en", "antes", "después", "que"}
_IGNORAR_ANTES = {"me", "te", "se", "nos", "no", "nunca", "tampoco"}


def infinitivo_sin_gobierno(nlp, texto, infinitivos):
    """True si en `texto` algún infinitivo de `infinitivos` quedó suelto: sin
    una preposición, "que" o un verbo modal justo antes ("No esta noche
    dormir", "mis jugar"). Un infinitivo así es una palabra sin conjugar."""
    doc = nlp(texto)
    for t in doc:
        if t.text.lower() not in infinitivos:
            continue
        j = t.i - 1
        while j >= 0 and doc[j].text.lower() in _IGNORAR_ANTES:
            j -= 1
        if j < 0:
            return True
        previo = doc[j]
        if previo.text.lower() in PREPOSICIONES_INF or previo.lemma_.lower() in GOBERNADORES:
            continue
        return True
    return False


def tiene_verbo_conjugado(nlp, texto):
    """True si la oración `texto` tiene algún verbo en forma personal (quiero,
    duele, dormí...). Se analiza la oración completa y no cada palabra suelta,
    porque el análisis morfológico de una palabra aislada es poco confiable
    ("puedo" solo no se reconoce como forma de "poder")."""
    return any(
        t.pos_ in ("VERB", "AUX") and "Fin" in t.morph.get("VerbForm")
        for t in nlp(texto)
    )


# ── Conjugación (primera persona singular) ───────────────────────────────────

_PRES_IRREG = {
    "ir": "voy", "ser": "soy", "estar": "estoy", "dar": "doy", "ver": "veo",
    "saber": "sé", "haber": "he", "tener": "tengo", "hacer": "hago",
    "poner": "pongo", "salir": "salgo", "venir": "vengo", "decir": "digo",
    "traer": "traigo", "caer": "caigo", "oír": "oigo", "valer": "valgo",
    "caber": "quepo", "conducir": "conduzco", "traducir": "traduzco",
}

# Cambio de raíz o irregularidad de la 1ª persona del presente
_PRES_RAIZ = {
    "dormir": "duermo", "poder": "puedo", "querer": "quiero", "pensar": "pienso",
    "empezar": "empiezo", "comenzar": "comienzo", "volver": "vuelvo",
    "jugar": "juego", "sentir": "siento", "pedir": "pido",
    "encontrar": "encuentro", "recordar": "recuerdo", "cerrar": "cierro",
    "perder": "pierdo", "entender": "entiendo", "contar": "cuento",
    "morir": "muero", "preferir": "prefiero", "mostrar": "muestro",
    "almorzar": "almuerzo", "seguir": "sigo", "elegir": "elijo",
    "repetir": "repito", "servir": "sirvo", "vestir": "visto",
    "despertar": "despierto", "mover": "muevo", "soñar": "sueño",
    "probar": "pruebo", "reír": "río", "corregir": "corrijo",
    "sentar": "siento", "acostar": "acuesto", "devolver": "devuelvo",
    "abrir": "abro",
}

_PRET_IRREG = {
    "ir": "fui", "ser": "fui", "dar": "di", "ver": "vi", "estar": "estuve",
    "tener": "tuve", "hacer": "hice", "poder": "pude", "poner": "puse",
    "querer": "quise", "saber": "supe", "venir": "vine", "decir": "dije",
    "traer": "traje", "andar": "anduve", "caber": "cupe", "conducir": "conduje",
    "traducir": "traduje", "haber": "hube", "reír": "reí", "oír": "oí",
}

# Verbos de estado: en una cláusula con "porque" siguen en presente
# ("porque tengo hambre"), a diferencia de las acciones ("porque no dormí").
ESTATIVOS = {
    "tener", "estar", "ser", "querer", "necesitar", "doler", "gustar", "saber",
    "poder", "sentir", "parecer", "preferir", "haber", "deber", "conocer",
    "odiar", "amar", "extrañar", "importar", "faltar", "molestar", "pesar",
}


def conjugar_yo(infinitivo, pasado=False):
    """Primera persona del singular de `infinitivo`, en presente o pretérito
    perfecto simple (`pasado=True`)."""
    v = infinitivo.lower()
    raiz, fin = v[:-2], v[-2:]
    if fin == "ír":  # reír, oír, sonreír
        fin = "ir"
    if pasado:
        if v in _PRET_IRREG:
            return _PRET_IRREG[v]
        if fin == "ar":
            # cambios ortográficos para conservar el sonido: buscar -> busqué,
            # jugar -> jugué, empezar -> empecé, averiguar -> averigüé
            if raiz.endswith("c"):
                return raiz[:-1] + "qué"
            if raiz.endswith("gu"):
                return raiz[:-1] + "üé"
            if raiz.endswith("g"):
                return raiz + "ué"
            if raiz.endswith("z"):
                return raiz[:-1] + "cé"
            return raiz + "é"
        return raiz + "í"  # incluye leer -> leí, caer -> caí, construir -> construí
    if v in _PRES_IRREG:
        return _PRES_IRREG[v]
    if v in _PRES_RAIZ:
        return _PRES_RAIZ[v]
    if fin in ("er", "ir"):
        if raiz.endswith(("c",)) and len(raiz) > 1 and raiz[-2] in "aeiouáéíóú":
            return raiz[:-1] + "zco"   # conocer, parecer, ofrecer
        if raiz.endswith("c"):
            return raiz[:-1] + "zo"    # vencer
        if raiz.endswith("g"):
            return raiz[:-1] + "jo"    # escoger, dirigir
        if raiz.endswith("gu"):
            return raiz[:-2] + "go"    # distinguir
        if raiz.endswith("u") and fin == "ir":
            return raiz + "yo"         # construir
    return raiz + "o"


# ── Armado de una cláusula simple ────────────────────────────────────────────

NEGACIONES = {"no", "nunca", "tampoco"}
CLITICOS = {"me", "te", "se", "nos"}
MOMENTOS = {"noche", "tarde", "madrugada"}          # "a la noche"
LUGARES = {                                         # sustantivo -> artículo
    "escuela": "la", "casa": None, "parque": "el", "plaza": "la", "baño": "el",
    "hospital": "el", "colegio": "el", "cole": "el", "playa": "la", "cine": "el",
    "club": "el", "cancha": "la", "cocina": "la", "pieza": "la",
    "habitación": "la", "patio": "el", "calle": "la", "kiosco": "el",
    "supermercado": "el", "negocio": "el", "biblioteca": "la", "farmacia": "la",
    "iglesia": "la", "trabajo": "el", "jardín": "el", "clínica": "la",
}
MOVIMIENTO = {"ir", "salir", "volver", "llegar", "venir", "entrar", "regresar"}
PROFESIONES = {                                     # "al médico", "a la maestra"
    "médico": "el", "doctor": "el", "dentista": "el", "profesor": "el",
    "maestro": "el", "enfermero": "el", "psicólogo": "el", "médica": "la",
    "doctora": "la", "profesora": "la", "maestra": "la", "enfermera": "la",
    "seño": "la", "psicóloga": "la",
}
FAMILIA = {
    "mamá", "papá", "abuela", "abuelo", "hermano", "hermana", "amigo", "amiga",
    "tío", "tía", "primo", "prima", "compañero", "compañera", "novio", "novia",
}
VERBOS_PERSONA_DIRECTA = {   # "vi a mi mamá" en vez de "vi con mi mamá"
    "ver", "llamar", "ayudar", "abrazar", "besar", "buscar", "esperar",
    "extrañar", "visitar", "saludar", "escuchar", "cuidar", "querer", "necesitar",
}
SIN_ARTICULO = {"hambre", "sed", "frío", "calor", "sueño", "miedo", "fiebre", "ganas", "dolor", "sueño", "tos", "vergüenza"}
MAX_PALABRAS_CLAUSULA = 4
NO_PERSONALES = {"doler", "gustar", "importar", "molestar", "faltar", "sobrar", "encantar", "parecer", "llover", "nevar", "pasar", "ocurrir"}
ADVERBIOS = {"mañana", "hoy", "ayer", "anoche", "ahora", "después", "antes", "temprano", "siempre", "nunca", "mucho", "poco", "rápido", "despacio", "acá", "allá", "acá", "afuera", "adentro"}
MASA = {"agua", "leche", "jugo", "pan", "comida", "ayuda", "plata", "dinero", "sopa", "arroz", "carne", "pollo", "fruta", "verdura", "helado", "café", "té", "gaseosa", "aire", "tiempo"}
FEMENINAS_CON_EL = {"agua", "águila", "alma", "área", "hacha", "arma", "ala", "hada"}
VERBOS_INDEFINIDO ={"comer", "tomar", "beber", "comprar", "necesitar", "tener", "pedir", "traer", "querer"}
_FEMENINAS_EN_O_A = {"mano": "la", "foto": "la", "moto": "la", "radio": "la", "día": "el", "mapa": "el", "problema": "el", "sofá": "el", "planeta": "el", "sistema": "el", "programa": "el", "idioma": "el"}


def _genero(nlp, sustantivo):
    """'la' o 'el' para un sustantivo."""
    s = sustantivo.lower()
    if s in _FEMENINAS_EN_O_A:
        return _FEMENINAS_EN_O_A[s]
    doc = nlp(s)
    if len(doc):
        g = doc[0].morph.get("Gender")
        if g:
            return "la" if g[0] == "Fem" else "el"
    return "la" if s.endswith(("a", "ión", "dad", "tad", "tud", "umbre", "z")) else "el"


def _prep_articulo(prep, articulo):
    """Contracciones: a+el -> al, de+el -> del."""
    if articulo == "el" and prep in ("a", "de"):
        return prep + "l"
    return f"{prep} {articulo}"


def componer_clausula(nlp, palabras, causa=False):
    """Arma una cláusula simple cuando la salida del modelo no sirve:
    [clíticos/negación] + verbo conjugado + complementos, usando cada palabra
    del usuario una sola vez. Devuelve la frase con mayúscula y punto, o None
    si no es una cláusula de un solo verbo en infinitivo (ahí el llamador parte
    la frase o cae al literal).

    `causa=True` indica que la cláusula viene después de "porque": las acciones
    van en pretérito ("porque no dormí") y los verbos de estado en presente."""
    # El pronombre sujeto se elide al conjugar ("yo comer" -> "como").
    palabras = [p.lower() for p in palabras if p.lower() not in OMITIBLES]
    if len(palabras) > MAX_PALABRAS_CLAUSULA:
        return None  # las reglas solo son confiables en cláusulas cortas
    infinitivos = [p for p in palabras if es_infinitivo(nlp, p)]
    if len(infinitivos) != 1:
        return None
    # Solo cláusulas claras: participios/adjetivos sueltos ("mojado", "roto") o
    # más de un sustantivo genérico ("romper ayuda auto") no se pueden armar
    # con reglas sin riesgo de decir algo distinto.
    if any(p.endswith(("ado", "ido", "ada", "ida")) or p in ("roto", "hecho", "puesto", "visto", "escrito") for p in palabras):
        return None
    if sum(_es_sustantivo_generico(nlp, p) for p in palabras) > 1:
        return None
    verbo = infinitivos[0]
    if verbo in NO_PERSONALES:
        return None  # "me duele", "me gusta": van en 3ª persona, lo arma el modelo
    if any(p in FUNCIONALES and p not in NEGACIONES | CLITICOS for p in palabras):
        return None  # preposiciones/conectores en el input: no sabemos dónde van
    if verbo in ("estar", "ser") and any(p not in NEGACIONES | CLITICOS and p != verbo for p in palabras):
        return None  # "estar tristeza": el complemento no lleva artículo, lo resuelve el modelo
    forma = conjugar_yo(verbo, pasado=causa and verbo not in ESTATIVOS)

    antes = [p for p in palabras if p in NEGACIONES or p in CLITICOS]
    # clíticos pegados al verbo, negación primero: "no me lastimé"
    antes.sort(key=lambda p: 0 if p in NEGACIONES else 1)
    despues = []
    for p in palabras:
        if p == verbo or p in antes:
            continue
        despues.append(_complemento(nlp, p, verbo))
    if not despues and not antes:
        return None  # un verbo solo: no hay nada que armar
    tokens = antes + [forma] + despues
    texto = " ".join(tokens)
    return texto[0].upper() + texto[1:] + "."


def _es_sustantivo_generico(nlp, palabra):
    """Sustantivo que no está en ninguna de las listas con reglas propias."""
    conocidas = (ADVERBIOS | MOMENTOS | set(LUGARES) | set(PROFESIONES) | FAMILIA
                 | SIN_ARTICULO | NEGACIONES | CLITICOS)
    return palabra not in conocidas and not es_infinitivo(nlp, palabra) and _pos(nlp, palabra) == "NOUN"


def _complemento(nlp, palabra, verbo):
    """Palabra suelta -> complemento con su preposición/artículo natural."""
    if palabra in ADVERBIOS:
        return palabra
    if palabra in MOMENTOS:
        return f"a la {palabra}"
    if palabra in LUGARES:
        art = LUGARES[palabra]
        prep = "a" if verbo in MOVIMIENTO else "en"
        return f"{prep} {palabra}" if art is None else f"{_prep_articulo(prep, art)} {palabra}"
    if palabra in PROFESIONES:
        return f"{_prep_articulo('a', PROFESIONES[palabra])} {palabra}"
    if palabra in FAMILIA:
        return f"{'a' if verbo in VERBOS_PERSONA_DIRECTA else 'con'} mi {palabra}"
    if _pos(nlp, palabra) == "NOUN" or palabra in SIN_ARTICULO:
        if palabra in SIN_ARTICULO or (palabra in MASA and verbo in VERBOS_INDEFINIDO):
            return palabra  # "tengo hambre", "quiero agua"
        art = _genero(nlp, palabra)
        if palabra in FEMENINAS_CON_EL:
            art = "el"      # "el agua", "un agua"
        if verbo in VERBOS_INDEFINIDO:
            art = "una" if art == "la" else "un"
        return f"{art} {palabra}"
    return palabra
