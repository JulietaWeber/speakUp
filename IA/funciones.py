import spacy
import numpy as np
import joblib
import os
import torch
from sklearn.neural_network import MLPClassifier
from modelo_correccion import (
    Encoder as EncoderCorreccion,
    Decoder as DecoderCorreccion,
    Vocabulario as VocabularioCorreccion,
    corregir_frase as _corregir_frase_modelo,
)

# ── Cargar spaCy (una sola vez al arrancar) ───────────────────────────────────

print("Cargando spaCy...")
nlp = spacy.load("es_core_news_md")
print("spaCy cargado\n")

# ── Cargar modelo base y encoders ─────────────────────────────────────────────

encoder_categoria = joblib.load("encoder_categoria.pkl")
encoder_salida    = joblib.load("encoder_salida.pkl")
modelo_base       = joblib.load("modelo_base.pkl")

# ── Cargar modelo de corrección de frases ─────────────────────────────────────

print("Cargando modelo de corrección...")
_checkpoint_correccion = torch.load("modelo_correccion.pt", map_location="cpu", weights_only=False)

_vocab_correccion = VocabularioCorreccion([])
_vocab_correccion.tok2idx = _checkpoint_correccion["tok2idx"]
_vocab_correccion.idx2tok = _checkpoint_correccion["idx2tok"]

_encoder_correccion = EncoderCorreccion(_checkpoint_correccion["dim_spacy"], _checkpoint_correccion["hidden_size"])
_decoder_correccion = DecoderCorreccion(len(_vocab_correccion), _checkpoint_correccion["hidden_size"], _checkpoint_correccion["emb_size"])
_encoder_correccion.load_state_dict(_checkpoint_correccion["encoder_state"])
_decoder_correccion.load_state_dict(_checkpoint_correccion["decoder_state"])
_encoder_correccion.eval()
_decoder_correccion.eval()
print("Modelo de corrección cargado\n")

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

# ── Función 3: Corregir frase ─────────────────────────────────────────────────

def corregir_frase(palabras):
    """Convierte una lista de palabras sueltas (sin orden ni conjugar) en una
    frase natural y correcta en español, usando el modelo entrenado en
    modelo_correccion.py."""
    return _corregir_frase_modelo(nlp, _encoder_correccion, _decoder_correccion, _vocab_correccion, palabras)