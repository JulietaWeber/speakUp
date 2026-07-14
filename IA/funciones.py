import spacy
import numpy as np
import joblib
import os
from sklearn.neural_network import MLPClassifier

# ── Cargar spaCy (una sola vez al arrancar) ───────────────────────────────────

print("Cargando spaCy...")
nlp = spacy.load("es_core_news_md")
print("spaCy cargado\n")

# ── Cargar modelo base y encoders ─────────────────────────────────────────────

encoder_categoria = joblib.load("encoder_categoria.pkl")
encoder_salida    = joblib.load("encoder_salida.pkl")
modelo_base       = joblib.load("modelo_base.pkl")

# ── Helpers ───────────────────────────────────────────────────────────────────

def palabra_a_vector(palabra):
    """Convierte una palabra a su vector spaCy de 96 dimensiones."""
    return nlp(palabra.lower()).vector

def categoria_a_vector(categoria):
    """Convierte una categoría a one-hot vector."""
    n = len(encoder_categoria.classes_)
    vector = np.zeros(n)
    vector[encoder_categoria.transform([categoria])[0]] = 1
    return vector

def cargar_modelo_usuario(user_id):
    """Carga el modelo del usuario si existe, sino usa el base."""
    path = f"modelos/modelo_{user_id}.pkl"
    if os.path.exists(path):
        return joblib.load(path)
    return modelo_base

# ── Función 1: Predecir Top 3 ─────────────────────────────────────────────────

def predecir_top3(user_id, categoria, palabra):
    modelo = cargar_modelo_usuario(user_id)

    entrada = np.concatenate([
        categoria_a_vector(categoria),
        palabra_a_vector(palabra)
    ]).reshape(1, -1)

    probs = modelo.predict_proba(entrada)[0]
    top3  = probs.argsort()[-3:][::-1]

    return [
        {
            "palabra":      encoder_salida.inverse_transform([modelo.classes_[i]])[0],
            "probabilidad": round(probs[i] * 100, 2)
        }
        for i in top3
    ]

# ── Función 2: Reentrenar ─────────────────────────────────────────────────────

def reentrenar(user_id, datos):
    nuevos_X = []
    nuevos_y = []

    for registro in datos:
        categoria = registro["categoria"]
        frase     = registro["frase"]

        for i in range(len(frase) - 1):
            palabra_actual    = frase[i]
            palabra_siguiente = frase[i + 1]

            if palabra_siguiente not in encoder_salida.classes_:
                print(f"'{palabra_siguiente}' no está en el vocabulario, se omite.")
                continue

            nuevos_X.append(np.concatenate([
                categoria_a_vector(categoria),
                palabra_a_vector(palabra_actual)
            ]))
            nuevos_y.append(encoder_salida.transform([palabra_siguiente])[0])

    if not nuevos_X:
        return {"status": "sin_datos"}

    nuevos_X = np.array(nuevos_X)
    nuevos_y = np.array(nuevos_y)

    path = f"modelos/modelo_{user_id}.pkl"
    if os.path.exists(path):
        modelo = joblib.load(path)
        modelo.set_params(warm_start=True, max_iter=100)
        modelo.fit(nuevos_X, nuevos_y)
    else:
        modelo = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation='relu',
            max_iter=500,
            random_state=42
        )
        modelo.fit(nuevos_X, nuevos_y)

    os.makedirs("modelos", exist_ok=True)
    joblib.dump(modelo, path)

    print(f"Modelo del usuario '{user_id}' actualizado con {len(nuevos_X)} pares.")
    return {"status": "ok", "pares_entrenados": len(nuevos_X)}