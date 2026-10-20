"""
Carga los modelos UNA sola vez al arrancar la API y expone las tres funciones
que usa api.py: predecir_top3, reentrenar y corregir_frase.

- spaCy (es_core_news_md): vectores de palabras y análisis morfológico.
  Se cargan solo los componentes que se usan (sin parser ni NER) para
  ahorrar memoria y tiempo.
- prediccion.Predictor: n-gramas Kneser-Ney (modelo_prediccion.npz/.json)
  + historial por usuario en modelos_usuarios/.
- correccion.Corrector: etiquetador de ediciones (modelo_correccion.npz/.json
  + lexico_correccion.json).
"""

import os

import spacy

from correccion import Corrector, correccion_basica
from prediccion import Predictor

AQUI = os.path.dirname(os.path.abspath(__file__))
# Carpeta donde se guarda el historial de cada usuario (/reentrenar). Se
# puede cambiar con la variable de entorno SPEAKUP_DIR_USUARIOS.
DIR_USUARIOS = os.environ.get("SPEAKUP_DIR_USUARIOS", os.path.join(AQUI, "modelos_usuarios"))

print("Cargando spaCy...")
nlp = spacy.load("es_core_news_md", exclude=["parser", "ner", "lemmatizer"])
_vectores = nlp.vocab.vectors


def vector_de(palabra):
    """Vector de spaCy de una palabra, o None (sin agregarla al vocabulario)."""
    fila = _vectores.key2row.get(nlp.vocab.strings[palabra])
    return None if fila is None else _vectores.data[fila]


print("Cargando modelo de predicción...")
predictor = Predictor(os.path.join(AQUI, "modelo_prediccion"), DIR_USUARIOS, vector_de)

print("Cargando modelo de corrección...")
_ARCHIVOS_CORRECCION = [os.path.join(AQUI, n) for n in
                        ("modelo_correccion.npz", "modelo_correccion.json", "lexico_correccion.json")]
if all(os.path.exists(p) for p in _ARCHIVOS_CORRECCION):
    corrector = Corrector(nlp, *_ARCHIVOS_CORRECCION)
else:
    # Respaldo: sin el modelo, /corregir igual responde (las palabras del
    # usuario con contracciones, mayúscula y puntuación; nunca inventa nada).
    print("AVISO: faltan los archivos del modelo de corrección, se usa la corrección básica")
    corrector = None

# Precalentar: la primera llamada inicializa cachés internas de spaCy/numpy.
predictor.predecir("_calentamiento", ["quiero"])
if corrector is not None:
    corrector.corregir(["quiero", "ir", "parque"])
print("Modelos listos\n")


def predecir_top3(user_id, palabras):
    """Las 3 palabras más probables después de `palabras` (hasta las últimas
    3 que escribió el usuario), con su probabilidad en porcentaje."""
    return predictor.predecir(user_id, palabras)


def reentrenar(user_id, datos):
    """Suma las frases del usuario a su historial personal (acumulativo)."""
    return predictor.reentrenar(user_id, datos)


def corregir_frase(palabras):
    """Frase casi correcta (lista de palabras) -> frase corregida."""
    if corrector is None:
        return correccion_basica(palabras)
    return corrector.corregir(palabras)
