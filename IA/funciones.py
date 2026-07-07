import fasttext
import numpy as np
import joblib
import os
from sklearn.neural_network import MLPClassifier

# ── Cargar fastText (una sola vez al arrancar) ────────────────────────────────

print("Cargando fastText...")
embeddings = fasttext.load_model("cc.es.300.bin")
print("fastText cargado\n")

# ── Cargar modelo base y encoders ─────────────────────────────────────────────

encoder_categoria = joblib.load("encoder_categoria.pkl")
encoder_salida    = joblib.load("encoder_salida.pkl")
modelo_base       = joblib.load("modelo_base.pkl")

# ── Helpers ───────────────────────────────────────────────────────────────────

def palabra_a_vector(palabra):
    return embeddings.get_word_vector(palabra.lower())

def categoria_a_vector(categoria):
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
    """
    Recibe un user_id, una categoría y una palabra.
    Devuelve las 3 palabras más probables para ese usuario.

    Ejemplo:
        predecir_top3("001", "Casa", "quiero")
        → [
            {"palabra": "comer",      "probabilidad": 45.2},
            {"palabra": "dormir",     "probabilidad": 30.1},
            {"palabra": "televisión", "probabilidad": 24.7}
          ]
    """
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
    """
    Recibe un user_id y una lista de frases de la semana.
    Reentrena el modelo del usuario con todos esos datos.

    Parámetro datos — lista de dicts con categoria y frase:
        [
            {"categoria": "Casa",    "frase": ["quiero", "ver", "televisión"]},
            {"categoria": "Escuela", "frase": ["necesito", "ayuda"]},
            {"categoria": "Médico",  "frase": ["me", "duele", "cabeza"]},
        ]
    """
    nuevos_X = []
    nuevos_y = []

    for registro in datos:
        categoria = registro["categoria"]
        frase     = registro["frase"]

        for i in range(len(frase) - 1):
            palabra_actual    = frase[i]
            palabra_siguiente = frase[i + 1]

            # Si la palabra de salida no está en el vocabulario, se omite
            if palabra_siguiente not in encoder_salida.classes_:
                print(f"'{palabra_siguiente}' no está en el vocabulario, se omite.")
                continue

            nuevos_X.append(np.concatenate([
                categoria_a_vector(categoria),
                palabra_a_vector(palabra_actual)
            ]))
            nuevos_y.append(encoder_salida.transform([palabra_siguiente])[0])

    if not nuevos_X:
        print(f"No hay datos válidos para reentrenar al usuario '{user_id}'.")
        return {"status": "sin_datos"}

    nuevos_X = np.array(nuevos_X)
    nuevos_y = np.array(nuevos_y)

    # Cargar modelo del usuario (o el base si es la primera vez)
    modelo = cargar_modelo_usuario(user_id)

    # Reentrenar desde donde quedó
    modelo.set_params(warm_start=True, max_iter=100)
    modelo.fit(nuevos_X, nuevos_y)

    # Guardar modelo personalizado del usuario
    os.makedirs("modelos", exist_ok=True)
    joblib.dump(modelo, f"modelos/modelo_{user_id}.pkl")

    print(f"Modelo del usuario '{user_id}' actualizado con {len(nuevos_X)} pares nuevos.")
    return {"status": "ok", "pares_entrenados": len(nuevos_X)}