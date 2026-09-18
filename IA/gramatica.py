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


def es_permitida(nlp, token, lemas_entrada):
    """True si `token` (una palabra de la frase de salida) es una palabra
    funcional cerrada o comparte lema con alguna de las palabras de entrada
    (`lemas_entrada`, ya calculados con `lema`)."""
    if not token.isalpha():
        return True  # puntuación, siempre permitida
    tl = token.lower()
    if tl in FUNCIONALES:
        return True
    lm = lema(nlp, token)
    if lm in FUNCIONALES:
        return True
    return lm in lemas_entrada
