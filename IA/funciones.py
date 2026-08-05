import spacy
import numpy as np
import joblib
import os
import copy
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

encoder_salida = joblib.load("encoder_salida.pkl")
modelo_base    = joblib.load("modelo_base.pkl")

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
    """Convierte una categoría a su vector spaCy, igual que las palabras.
    Así el modelo acepta cualquier categoría nueva sin necesitar reentrenar."""
    return nlp(categoria.lower()).vector

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
    try:
        # Siempre se parte del modelo base (no del modelo previo del usuario),
        # así el modelo personalizado conserva el conocimiento general y no se
        # sesga con las primeras frases que usó. Se usa partial_fit en vez de
        # fit(warm_start=True): en MLPClassifier, fit() con warm_start exige
        # que las clases del batch nuevo coincidan EXACTO con las del modelo
        # previo, algo que casi nunca pasa con un batch semanal chico. partial_fit
        # sigue entrenando sobre los pesos existentes sin esa restricción.
        modelo = copy.deepcopy(modelo_base)
        modelo.partial_fit(nuevos_X, nuevos_y)
    except ValueError:
        # Los datos nuevos son incompatibles con el modelo base (p. ej. clases
        # fuera del vocabulario conocido). Se entrena un modelo nuevo desde cero.
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