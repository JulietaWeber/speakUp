from fastapi import FastAPI
from pydantic import BaseModel

from funciones import corregir_frase, predecir_top3, reentrenar

# ── Crear la app ──────────────────────────────────────────────────────────────
# "app" es la variable que busca el servidor cuando ejecuta "uvicorn api:app".
# Los modelos se cargan una sola vez al importar funciones.py.

app = FastAPI(title="SpeakUp IA")

# ── Modelos de datos ──────────────────────────────────────────────────────────
# Le decimos a FastAPI exactamente qué datos esperamos recibir en cada endpoint.
# Si el back manda algo mal formado, FastAPI lo rechaza automáticamente (422).


class PredecirRequest(BaseModel):
    user_id: str
    palabras: list[str] = []  # últimas hasta 3 palabras escritas por el usuario, en orden


class ReentrenarRequest(BaseModel):
    user_id: str
    datos: list  # lista de {"categoria": "Casa", "frase": ["quiero", "comer"]}


class CorregirRequest(BaseModel):
    palabras: list  # palabras de la frase, en orden, ej: ["quiero", "ir", "parque"]


# ── Endpoint 1: Predecir ──────────────────────────────────────────────────────
# El back llama a este endpoint con un user_id y las últimas hasta 3 palabras
# que escribió el usuario (si escribió menos de 3, manda las que tenga; si
# todavía no escribió nada, una lista vacía). Devuelve SIEMPRE 3 palabras.
#
# Ejemplo de request:
#   POST /predecir
#   {"user_id": "001", "palabras": ["quiero", "ir", "al"]}
#
# Ejemplo de response:
#   [
#     {"palabra": "baño",   "probabilidad": 18.4},
#     {"palabra": "parque", "probabilidad": 12.9},
#     {"palabra": "club",   "probabilidad": 9.7}
#   ]


@app.post("/predecir")
def predecir(request: PredecirRequest):
    return predecir_top3(request.user_id, request.palabras)


# ── Endpoint 2: Reentrenar ────────────────────────────────────────────────────
# El back llama a este endpoint (por ejemplo una vez por semana) con las
# frases que usó el usuario. Se suman a su historial personal y desde ese
# momento /predecir le da más peso a lo que ese usuario suele decir.
#
# Ejemplo de request:
#   POST /reentrenar
#   {
#     "user_id": "001",
#     "datos": [
#       {"categoria": "Casa",    "frase": ["quiero", "ver", "televisión"]},
#       {"categoria": "Escuela", "frase": ["necesito", "ayuda"]}
#     ]
#   }
#
# Ejemplo de response:
#   {"status": "ok", "pares_entrenados": 5}


@app.post("/reentrenar")
def reentrenar_modelo(request: ReentrenarRequest):
    return reentrenar(request.user_id, request.datos)


# ── Endpoint 3: Corregir frase ────────────────────────────────────────────────
# El back manda las palabras (pictogramas) que fue eligiendo el usuario, en
# orden, y recibe la frase completa y corregida: completa lo que se puede
# deducir (["triste"] -> "Estoy triste.", ["mamá", "agua"] -> "Mamá, quiero
# agua.") y corrige artículos, preposiciones, concordancia, tildes, mayúscula
# y puntuación. Las palabras del usuario aparecen siempre, en su orden: solo
# se agregan palabras, nunca se borran ni se cambian por otras. Si no se
# puede deducir nada útil, vuelven las mismas palabras con mayúscula y punto.
#
# Ejemplo de request:
#   POST /corregir
#   {"palabras": ["quiero", "ir", "parque", "con", "mi", "mamá"]}
#
# Ejemplo de response:
#   {"frase": "Quiero ir al parque con mi mamá."}


@app.post("/corregir")
def corregir(request: CorregirRequest):
    return {"frase": corregir_frase(request.palabras)}


# ── Endpoint 4: Health check ──────────────────────────────────────────────────
# Para verificar que la API está corriendo.
#   GET /  ->  {"status": "ok"}


@app.get("/")
def health_check():
    return {"status": "ok"}


# ── Endpoint 5: Ping ──────────────────────────────────────────────────────────
# Endpoint liviano para que un servicio externo (UptimeRobot) le pegue cada
# pocos minutos y evite que el servidor gratuito se duerma por inactividad.
#   GET /ping  ->  {"status": "ok"}


@app.get("/ping")
def ping():
    return {"status": "ok"}
