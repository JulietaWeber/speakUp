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
_NO_TERMINA =_DETERMINANTES | _PREPOSICIONES | _NEXOS | {"muy", "más", "menos", "tan", "me", "te", "se", "nos", "le", "les"}


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
        if t in _DETERMINANTES and sig in (_DETERMINANTES | _PREPOSICIONES | _NEXOS | _PRONOMBRES_SUJETO):
            return False
        if t in _PREPOSICIONES and sig in (_NEXOS | _CLITICOS | _PRONOMBRES_SUJETO):
            return False
        if t in _CLITICOS and sig in _DETERMINANTES_MASC_SING:
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


def token_cubre(nlp, token, palabra):
    """True si `token` (de la salida) representa a `palabra` (de la entrada),
    directamente o por lema (conjugación / plural)."""
    if not token.isalpha():
        return False
    tl = token.lower()
    lema_palabra = lema(nlp, palabra)
    return tl in (palabra, lema_palabra) or lema(nlp, tl) in (palabra, lema_palabra)


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
    (`lemas_entrada`, ya calculados con `lema`)."""
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
    return lm in lemas_entrada
