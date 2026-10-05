"""Entrenamiento del modelo base de predicción de la siguiente palabra.

Cambio de diseño respecto a la versión anterior (ver IA/modelo_anterior/):
antes el modelo recibía categoría + una palabra. Ahora recibe directamente
el CONTEXTO: las últimas hasta 3 palabras que fue escribiendo el usuario
(1, 2 o 3, según cuántas haya disponibles), sin categoría. Esto le da al
modelo más contexto real para predecir mejor la palabra siguiente, y hace
que /predecir ya no dependa de que el back mande una categoría.

Este script NO se ejecutó todavía (no se entrenó el modelo nuevo). Está
listo para correrse con: python modelo_final.py
"""

import numpy as np
import joblib
import spacy
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from dataset_predictivo import PARES

# ── Cargar modelo spaCy en español ───────────────────────────────────────────

print("Cargando spaCy...")
nlp = spacy.load("es_core_news_md")
print("spaCy cargado\n")

DIM_SPACY = 96       # dimensión de los vectores de es_core_news_md
MAX_CONTEXTO = 3      # cantidad máxima de palabras de contexto que usa el modelo

# ── Vectorización de contexto ────────────────────────────────────────────────
# El modelo siempre recibe un vector de tamaño fijo MAX_CONTEXTO * DIM_SPACY.
# Si el contexto tiene menos de 3 palabras, se rellena con ceros a la
# IZQUIERDA, de manera que la palabra más reciente siempre caiga en la
# misma posición final del vector (el bloque más a la derecha). Así el
# modelo aprende de forma consistente dónde está "la última palabra",
# "la anteúltima", etc., sin importar cuántas palabras haya en el contexto.

def palabra_a_vector(palabra):
    """Convierte una palabra a su vector spaCy de 96 dimensiones."""
    return nlp(palabra.lower()).vector

def contexto_a_vector(contexto):
    """Convierte una lista de hasta 3 palabras (las últimas escritas por el
    usuario, en orden) en un único vector de tamaño fijo, rellenando con
    ceros a la izquierda si hay menos de 3 palabras."""
    contexto = contexto[-MAX_CONTEXTO:]
    faltantes = MAX_CONTEXTO - len(contexto)
    bloques = [np.zeros(DIM_SPACY) for _ in range(faltantes)]
    bloques += [palabra_a_vector(p) for p in contexto]
    return np.concatenate(bloques)

# ── Encoders ──────────────────────────────────────────────────────────────────

encoder_salida = LabelEncoder()
encoder_salida.fit([siguiente for _, siguiente in PARES])

# ── Construcción de X e y ─────────────────────────────────────────────────────

print(f"Pares de entrenamiento: {len(PARES)}")
print("Vectorizando contextos con spaCy (puede tardar varios minutos)...")

X, y = [], []
for contexto, siguiente in PARES:
    X.append(contexto_a_vector(contexto))
    y.append(encoder_salida.transform([siguiente])[0])

X = np.array(X)
y = np.array(y)

# ── División training / testing ───────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training: {len(X_train)} | Testing: {len(X_test)}\n")

# ── Red Neuronal ──────────────────────────────────────────────────────────────

modelo = MLPClassifier(
    hidden_layer_sizes=(256, 128),
    activation='relu',
    max_iter=500,
    random_state=42
)

print("Entrenando modelo...")
modelo.fit(X_train, y_train)
print("Entrenamiento completo\n")

# ── Métricas ──────────────────────────────────────────────────────────────────

def hit_rate_at_k(modelo, X_test, y_test, k=3):
    hits = 0
    probs = modelo.predict_proba(X_test)
    for i, p in enumerate(probs):
        top_k = modelo.classes_[p.argsort()[-k:][::-1]]
        if y_test[i] in top_k:
            hits += 1
    return hits / len(y_test)

print(f"Hit Rate@3: {hit_rate_at_k(modelo, X_test, y_test, k=3) * 100:.2f}%\n")

# ── Guardar modelo ────────────────────────────────────────────────────────────

joblib.dump(modelo, "modelo_base.pkl")
joblib.dump(encoder_salida, "encoder_salida.pkl")
# Se guardan también los pares (X, y) originales usados para entrenar el
# modelo base. funciones.py los usa para el reentrenamiento acumulativo: cada
# vez que un usuario reentrena, se reentrena un modelo fresco sobre la unión
# de estos pares base + todo el historial acumulado del usuario, así el
# modelo final siempre conserva el conocimiento general (A) además de todo lo
# que el usuario fue enseñando (B, C, ...).
joblib.dump((X, y), "base_pares.pkl")
print("Modelo guardado: modelo_base.pkl\n")

# ── Prueba ────────────────────────────────────────────────────────────────────

print("── Prueba de predicciones ──")
ejemplos = [
    ["quiero"],
    ["quiero", "ver"],
    ["quiero", "ver", "televisión"],
    ["necesito"],
    ["me", "duele"],
    ["estoy"],
    ["tengo", "mucho"],
    ["quiero", "ir", "a"],
]

for contexto in ejemplos:
    entrada = contexto_a_vector(contexto).reshape(1, -1)
    probs = modelo.predict_proba(entrada)[0]
    top3 = probs.argsort()[-3:][::-1]
    print(f"\n{contexto}:")
    for i in top3:
        p = encoder_salida.inverse_transform([modelo.classes_[i]])[0]
        print(f"  - {p} ({round(probs[i]*100, 2)}%)")
