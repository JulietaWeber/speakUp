"""
Vocabulario cerrado de "palabras funcionales" (glue gramatical) que el modelo
de corrección tiene permitido usar aunque NO vengan en las palabras que
seleccionó el usuario: artículos, preposiciones, conjunciones, pronombres,
posesivos, demostrativos y un grupo chico de negación/intensificadores.

Todo lo demás -verbos, sustantivos, adjetivos, adverbios de contenido- tiene
que venir SIEMPRE en las palabras de entrada: el modelo arma la frase
reordenando y conjugando esas palabras, pero no puede inventar contenido
nuevo. Este archivo lo usan tanto dataset_correccion.py (para validar que
cada ejemplo del dataset respete la regla) como modelo_correccion.py (para
enmascarar en inferencia cualquier palabra de salida que no sea ni funcional
ni derivada de la entrada).
"""

FUNCIONALES = {
    # artículos
    "el", "la", "los", "las", "un", "una", "unos", "unas", "lo", "al", "del",
    # preposiciones
    "a", "ante", "bajo", "con", "contra", "de", "desde", "en", "entre",
    "hacia", "hasta", "para", "por", "según", "sin", "sobre", "tras",
    # conjunciones
    "y", "e", "o", "u", "pero", "porque", "que", "si", "cuando", "como",
    "aunque", "ni", "sino", "pues",
    # pronombres personales / reflexivos / de objeto
    "yo", "tú", "vos", "usted", "él", "ella", "nosotros", "nosotras",
    "ustedes", "ellos", "ellas", "me", "te", "se", "nos", "os", "le", "les",
    "mí", "ti", "sí", "conmigo", "contigo", "consigo",
    # posesivos
    "mi", "mis", "tu", "tus", "su", "sus", "nuestro", "nuestra", "nuestros",
    "nuestras", "vuestro", "vuestra", "vuestros", "vuestras",
    # demostrativos
    "este", "esta", "estos", "estas", "esto", "ese", "esa", "esos", "esas",
    "eso", "aquel", "aquella", "aquellos", "aquellas", "aquello",
    # negación / intensificadores (glue cerrado, no "inventan" contenido)
    "no", "muy", "más", "menos", "tan", "también", "tampoco", "ya",
}

# Funcionales que SÍ cambian el significado si se agregan (negación,
# intensidad, causa, contraste...): solo se pueden generar si el usuario las
# eligió. El resto de FUNCIONALES (artículos, preposiciones, "y", "que",
# pronombres, posesivos, demostrativos) es glue puro y se puede agregar.
SOLO_SI_EN_ENTRADA = {
    "no", "ni", "tampoco", "muy", "más", "menos", "tan", "ya", "también",
    "pero", "porque", "aunque", "sino", "si", "cuando", "pues", "o", "u",
    "sin", "contra", "desde", "hasta", "tras", "ante", "bajo", "sobre",
    "según", "entre", "hacia",
    # pronombres sujeto: inventarlos introduce un referente que el usuario no
    # eligió ("ella"); el sujeto ya va implícito en la conjugación del verbo.
    "yo", "tú", "vos", "usted", "él", "ella", "nosotros", "nosotras",
    "ustedes", "ellos", "ellas",
    # tónicos y "nos": en frases largas el modelo los usaba de relleno ("una
    # mochila de mí", "nos de la cuento"), sumando un referente nuevo.
    "mí", "ti", "sí", "consigo", "nos", "os",
}

_DETERMINANTES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "al", "del",
    "mi", "mis", "tu", "tus", "su", "sus", "nuestro", "nuestra", "nuestros",
    "nuestras", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
}
_PREPOSICIONES = {
    "a", "ante", "bajo", "con", "contra", "de", "desde", "en", "entre",
    "hacia", "hasta", "para", "por", "según", "sin", "sobre", "tras",
}
_NEXOS = {"y", "e", "o", "u", "que", "porque", "pero", "si", "cuando", "como", "aunque", "pues"}
_CIERRES = {".", "!", "?", "¿", "¡"}
_CLITICOS = {"me", "te", "se", "nos", "le", "les"}
_PRONOMBRES_SUJETO = {"yo", "tú", "vos", "usted", "él", "ella", "nosotros", "nosotras", "ustedes", "ellos", "ellas"}
_DETERMINANTES_MASC_SING = {"el", "al", "del", "un", "mi", "tu", "su"}
_NO_TERMINA =_DETERMINANTES | _PREPOSICIONES | _NEXOS | {"muy", "más", "menos", "tan", "me", "te", "se", "nos", "le", "les", "lo"}
_TONICOS = {"conmigo", "contigo", "consigo", "mí", "ti", "sí"}


def bien_formada(tokens):
    """Chequeo estructural mínimo sobre la salida del modelo: rechaza frases
    colgadas ("Voy a la.", "Quiero mi la escuela", "por el,"): un determinante,
    preposición, nexo o clítico no puede quedar al final de la frase o de un
    tramo (antes de coma/punto), ni un determinante seguido de otro
    determinante o de una preposición."""
    toks = [t.lower() for t in tokens]
    for i, t in enumerate(toks):
        sig = toks[i + 1] if i + 1 < len(toks) else None
        # Mayúscula en medio de la frase ("... en la Me al ..."): solo es
        # válida al inicio o después de un punto / signo de cierre.
        if i > 0 and tokens[i][:1].isupper() and toks[i - 1] not in _CIERRES:
            return False
        if t in _NO_TERMINA and (sig is None or not sig.isalpha()):
            return False
        if sig == t and t.isalpha():
            return False  # "de de", "quiero quiero"
        if t in _DETERMINANTES and sig in (_DETERMINANTES | _PREPOSICIONES | _NEXOS | _PRONOMBRES_SUJETO | _TONICOS
                                           | {"mucho", "mucha", "muchos", "muchas", "muy"}):
            return False
        if t in _PREPOSICIONES and sig in (_NEXOS | _CLITICOS | _PRONOMBRES_SUJETO | {"conmigo", "contigo", "consigo"}):
            return False
        if t in _CLITICOS and sig in _DETERMINANTES_MASC_SING:
            return False
    return True


def verbo_tras_preposicion(tokens, palabras):
    """True si una forma conjugada de un infinitivo de la entrada quedó justo
    después de una preposición ("a corrí", "de juego"): ahí va el
    infinitivo ("a correr"). Las formas se calculan con `formas`, así que no
    depende del análisis de spaCy sobre una frase posiblemente rota."""
    from conjugacion import formas_verbales
    conjugadas = set()
    for p in palabras:
        conjugadas |= formas_verbales(p) - {p.lower()}
    toks = [t.lower() for t in tokens]
    return any(toks[i - 1] in _PREPOSICIONES and toks[i] in conjugadas for i in range(1, len(toks)))


# ── Concordancia de género y número ──────────────────────────────────────────
# El género de un sustantivo no se puede sacar de spaCy en la frase generada
# (lo infiere justamente del artículo que tiene al lado: en "el flor" etiqueta
# "flor" como masculino). Por eso se aprende de las frases correctas del
# dataset: qué determinantes acompañan a cada sustantivo ("la flor", "el agua",
# "las piernas"), y en inferencia se rechazan las hipótesis que no concuerden.

_GENERO_DET = {
    "el": ("m", "s"), "al": ("m", "s"), "del": ("m", "s"), "un": ("m", "s"),
    "la": ("f", "s"), "una": ("f", "s"), "los": ("m", "p"), "unos": ("m", "p"),
    "las": ("f", "p"), "unas": ("f", "p"), "este": ("m", "s"), "esta": ("f", "s"),
    "estos": ("m", "p"), "estas": ("f", "p"), "ese": ("m", "s"), "esa": ("f", "s"),
    "esos": ("m", "p"), "esas": ("f", "p"), "mucho": ("m", "s"), "mucha": ("f", "s"),
    "muchos": ("m", "p"), "muchas": ("f", "p"), "mi": (None, "s"), "mis": (None, "p"),
    "tu": (None, "s"), "tus": (None, "p"), "su": (None, "s"), "sus": (None, "p"),
}
# Femeninos con "el"/"un" por empezar con a tónica ("el agua fría").
FEMENINAS_CON_EL = {"agua", "águila", "alma", "área", "hacha", "arma", "ala", "hada", "hambre"}


def _rasgos_det(det, sustantivo):
    g, n = _GENERO_DET[det]
    if g == "m" and n == "s" and det in ("el", "al", "del", "un") and sustantivo in FEMENINAS_CON_EL:
        g = "f"
    return g, n


def lexico_genero(oraciones_tokenizadas):
    """{sustantivo: {(género, número), ...}} a partir de los determinantes que
    lo preceden en frases correctas."""
    lex = {}
    for toks in oraciones_tokenizadas:
        for i in range(1, len(toks)):
            det, sust = toks[i - 1].lower(), toks[i].lower()
            if det in _GENERO_DET and sust.isalpha() and sust not in FUNCIONALES and _GENERO_DET[det][0]:
                lex.setdefault(sust, set()).add(_rasgos_det(det, sust))
    return lex


def flexionar(adj, genero, numero="s"):
    """Adjetivo en forma base (masc. sing.) -> forma concordada."""
    if adj.endswith("o"):
        base = adj[:-1] + ("a" if genero == "f" else "o")
        return base + ("s" if numero == "p" else "")
    if numero == "s":
        return adj
    if adj.endswith("z"):
        return adj[:-1] + "ces"
    return adj + ("s" if adj.endswith("e") else "es")


def rasgos_adjetivo(adj):
    if adj.endswith("os"):
        return "m", "p"
    if adj.endswith("as"):
        return "f", "p"
    if adj.endswith("o"):
        return "m", "s"
    if adj.endswith("a"):
        return "f", "s"
    return None, "p" if adj.endswith("es") else "s"


def _compatible(rasgos, posibles):
    g, n = rasgos
    return any((g is None or g == pg) and n == pn for pg, pn in posibles)


def concuerda(tokens, lex, adjetivos):
    """False si hay un determinante o adjetivo que no concuerda con el
    sustantivo al que acompaña ("el flor", "los película", "un sándwich
    rica"). Solo se juzgan sustantivos con género conocido (`lex`) y, como
    adjetivos, las formas de palabras de la entrada que son adjetivos
    (`adjetivos`): ante la duda, no se rechaza."""
    toks = [t.lower() for t in tokens]
    for i in range(1, len(toks)):
        prev, t = toks[i - 1], toks[i]
        if prev in _GENERO_DET and t in lex and not _compatible(_rasgos_det(prev, t), lex[t]):
            return False
        if t in adjetivos and prev in lex and not _compatible(rasgos_adjetivo(t), lex[prev]):
            return False
    return True


_cache_lemas = {}


def lema(nlp, palabra):
    """Lema (forma base) de una palabra suelta, en minúscula y cacheado.

    Se usa tanto para validar el dataset como para enmascarar en inferencia,
    así que las dos etapas tienen que evaluar la misma palabra exactamente
    igual (por eso se cachea acá y no en cada módulo por separado)."""
    clave = palabra.lower()
    if clave not in _cache_lemas:
        doc = nlp(clave)
        _cache_lemas[clave] = doc[0].lemma_.lower() if len(doc) else clave
    return _cache_lemas[clave]


# Lo único de la entrada que se puede omitir sin perder contenido: el pronombre
# sujeto (se elide al conjugar: "yo quiero" -> "Quiero") y los artículos.
# Conectores (porque, y, con, para...), negaciones y todo lo demás son
# obligatorios: omitirlos cambia el significado de la frase.
OMITIBLES = {
    "yo", "tú", "vos", "usted", "él", "ella", "nosotros", "nosotras",
    "ustedes", "ellos", "ellas",
    "el", "la", "los", "las", "un", "una", "unos", "unas",
}

CONJUNCIONES = {"porque", "y", "e", "pero", "cuando", "si", "aunque", "pues", "o", "u", "ni", "sino"}


def palabras_obligatorias(palabras):
    """Palabras de la entrada que la frase generada NO puede omitir."""
    return [p.lower() for p in palabras if p.lower() not in OMITIBLES]


_cache_formas = {}


def formas(palabra):
    """Flexiones de `palabra` (de la entrada) que la frase de salida puede
    usar en su lugar: género/número de adjetivos y sustantivos ("frío" ->
    "fría", "frías") y conjugaciones de verbos en infinitivo ("dibujar" ->
    "dibujé", "dibuja", "dibujamos"...). Complementa a `lema`, porque spaCy
    lematiza mal muchas formas sueltas ("dibujé", "enferma", "contenta") y sin
    esto la máscara de vocabulario bloqueaba frases correctas. Son siempre
    formas de la MISMA palabra: no habilitan contenido nuevo."""
    p = palabra.lower()
    if p in _cache_formas:
        return _cache_formas[p]
    res = {p}
    # género y número
    if p.endswith("o"):
        res |= {p[:-1] + "a", p + "s", p[:-1] + "as"}
    elif p.endswith("a"):
        res |= {p + "s", p[:-1] + "o", p[:-1] + "os"}
    elif p.endswith("e"):
        res.add(p + "es")
    elif p.endswith("z"):
        res.add(p[:-1] + "ces")
    elif p[-1:].isalpha() and p[-1] not in "áéíóús":
        res.add(p + "es")
    # conjugaciones (import diferido: conjugacion importa este módulo)
    from conjugacion import formas_verbales
    res |= formas_verbales(p)
    # Una flexión nunca puede habilitar una funcional ("pera" -> "pero").
    res = {f for f in res if f == p or f not in FUNCIONALES}
    _cache_formas[p] = res
    return res


def lemas_y_formas(nlp, palabras):
    """Conjunto contra el que se valida cada token de salida (ver
    `es_permitida`): lemas de las palabras de entrada más sus flexiones."""
    conjunto = set()
    for p in palabras:
        conjunto.add(lema(nlp, p))
        conjunto |= formas(p)
    return conjunto


def token_cubre(nlp, token, palabra):
    """True si `token` (de la salida) representa a `palabra` (de la entrada),
    directamente, por lema o por flexión (conjugación / género / plural)."""
    if not token.isalpha():
        return False
    tl = token.lower()
    lema_palabra = lema(nlp, palabra)
    return (tl in (palabra, lema_palabra) or lema(nlp, tl) in (palabra, lema_palabra)
            or tl in formas(palabra))


def cubre_entrada(nlp, tokens_salida, palabras):
    """True si la frase generada (`tokens_salida`) contiene TODAS las palabras
    obligatorias de la entrada (ver `palabras_obligatorias`)."""
    return all(
        any(token_cubre(nlp, t, p) for t in tokens_salida)
        for p in palabras_obligatorias(palabras)
    )


def es_permitida(nlp, token, lemas_entrada):
    """True si `token` (una palabra de la frase de salida) es una palabra
    funcional cerrada o comparte lema con alguna de las palabras de entrada
    (`lemas_entrada`, calculados con `lemas_y_formas`, que incluye además las
    flexiones de cada palabra)."""
    if not token.isalpha():
        return True  # puntuación, siempre permitida
    tl = token.lower()
    lm = lema(nlp, token)
    if tl in SOLO_SI_EN_ENTRADA:
        return tl in lemas_entrada or lm in lemas_entrada
    if tl in FUNCIONALES:
        return True
    if lm in FUNCIONALES:
        return lm not in SOLO_SI_EN_ENTRADA or lm in lemas_entrada
    return lm in lemas_entrada or tl in lemas_entrada
