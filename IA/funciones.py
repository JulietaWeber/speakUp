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

encoder_salida = joblib.load("encoder_salida.pkl")
modelo_base    = joblib.load("modelo_base.pkl")
X_base, y_base = joblib.load("base_pares.pkl")

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
            "probabilidad": float(round(probs[i] * 100, 2))
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

    os.makedirs("modelos", exist_ok=True)
    modelo_path    = f"modelos/modelo_{user_id}.pkl"
    historial_path = f"modelos/historial_{user_id}.pkl"

    # Reentrenamiento acumulativo: se guarda el historial completo de pares
    # (categoría+palabra -> palabra siguiente) de TODOS los reentrenamientos
    # anteriores del usuario, y en cada llamada se reentrena un modelo FRESCO
    # sobre la unión de los pares base (A) + histórico del usuario + lote
    # nuevo. Así, si el usuario reentrena con B y después con C, el modelo
    # final tiene A+B+C en vez de perder B (que es lo que pasaba al partir
    # siempre del modelo base con solo el lote nuevo).
    #
    # No se usa partial_fit ni fit(warm_start=True): en MLPClassifier ambos
    # exigen que el conjunto de clases de cada llamada sea EXACTAMENTE igual
    # al de la llamada anterior (ValueError en caso contrario), algo que no
    # se puede garantizar de antemano porque cada usuario puede introducir
    # palabras nuevas en cualquier reentrenamiento. Al incluir siempre los
    # pares base A en el fit, un modelo fresco por reentrenamiento no pierde
    # el conocimiento general y evita por completo esa restricción de clases.
    if os.path.exists(historial_path):
        hist_X, hist_y = joblib.load(historial_path)
        hist_X = np.concatenate([hist_X, nuevos_X])
        hist_y = np.concatenate([hist_y, nuevos_y])
    else:
        hist_X, hist_y = nuevos_X, nuevos_y

    joblib.dump((hist_X, hist_y), historial_path)

    X_total = np.concatenate([X_base, hist_X])
    y_total = np.concatenate([y_base, hist_y])

    modelo = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        max_iter=500,
        random_state=42
    )
    modelo.fit(X_total, y_total)

    joblib.dump(modelo, modelo_path)

    print(f"Modelo del usuario '{user_id}' actualizado con {len(nuevos_X)} pares nuevos ({len(hist_X)} acumulados del usuario + {len(X_base)} base).")
    return {"status": "ok", "pares_entrenados": len(nuevos_X)}

# ── Función 3: Corregir frase ─────────────────────────────────────────────────

def corregir_frase(palabras):
    """Convierte una lista de palabras sueltas (sin orden ni conjugar) en una
    frase natural y correcta en español, usando el modelo entrenado en
    modelo_correccion.py."""
    return _corregir_frase_modelo(nlp, _encoder_correccion, _decoder_correccion, _vocab_correccion, palabras)