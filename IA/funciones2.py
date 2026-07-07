import numpy as np
import joblib
import os
from sklearn.neural_network import MLPClassifier

# ── Cargar modelo base y encoders ─────────────────────────────────────────────

encoder_categoria = joblib.load("encoder_categoria.pkl")
encoder_palabra   = joblib.load("encoder_palabra.pkl")
modelo_base       = joblib.load("modelo_base.pkl")

# ── Helper ────────────────────────────────────────────────────────────────────

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
            {"palabra": "comer",  "probabilidad": 45.2},
            {"palabra": "dormir", "probabilidad": 30.1},
            {"palabra": "jugar",  "probabilidad": 24.7}
          ]
    """
    # Verificar que la palabra esté en el vocabulario
    if palabra not in encoder_palabra.classes_:
        return [{"error": f"La palabra '{palabra}' no está en el vocabulario"}]

    modelo = cargar_modelo_usuario(user_id)

    entrada = [[
        encoder_categoria.transform([categoria])[0],
        encoder_palabra.transform([palabra])[0]
    ]]

    probs  = modelo.predict_proba(entrada)[0]
    top3   = probs.argsort()[-3:][::-1]

    return [
        {
            "palabra":      encoder_palabra.inverse_transform([modelo.classes_[i]])[0],
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

            # Verificar que ambas palabras estén en el vocabulario
            if palabra_actual not in encoder_palabra.classes_:
                print(f"'{palabra_actual}' no está en el vocabulario, se omite.")
                continue
            if palabra_siguiente not in encoder_palabra.classes_:
                print(f"'{palabra_siguiente}' no está en el vocabulario, se omite.")
                continue

            nuevos_X.append([
                encoder_categoria.transform([categoria])[0],
                encoder_palabra.transform([palabra_actual])[0]
            ])
            nuevos_y.append(encoder_palabra.transform([palabra_siguiente])[0])

    if not nuevos_X:
        print(f"No hay datos válidos para reentrenar al usuario '{user_id}'.")
        return {"status": "sin_datos"}

    nuevos_X = np.array(nuevos_X)
    nuevos_y = np.array(nuevos_y)

    modelo = cargar_modelo_usuario(user_id)
    modelo.set_params(warm_start=True, n_estimators=150)
    modelo.fit(nuevos_X, nuevos_y)

    os.makedirs("modelos", exist_ok=True)
    joblib.dump(modelo, f"modelos/modelo_{user_id}.pkl")

    print(f"Modelo del usuario '{user_id}' actualizado con {len(nuevos_X)} pares nuevos.")
    return {"status": "ok", "pares_entrenados": len(nuevos_X)}
