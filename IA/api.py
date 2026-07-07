from fastapi import FastAPI
from pydantic import BaseModel
from funciones2 import predecir_top3, reentrenar

# ── Crear la app ──────────────────────────────────────────────────────────────
# "app" es la variable que Railway busca cuando ejecuta "uvicorn api:app"

app = FastAPI()

# ── Modelos de datos ──────────────────────────────────────────────────────────
# Le decimos a FastAPI exactamente qué datos esperamos recibir en cada endpoint.
# Si el back manda algo mal formado, FastAPI lo rechaza automáticamente.

class PredecirRequest(BaseModel):
    user_id:   str
    categoria: str
    palabra:   str

class ReentrenarRequest(BaseModel):
    user_id: str
    datos:   list  # lista de {"categoria": "Casa", "frase": ["quiero", "comer"]}

# ── Endpoint 1: Predecir ──────────────────────────────────────────────────────
# El back llama a este endpoint con un user_id, categoria y palabra.
# Devuelve las 3 palabras más probables para ese usuario.
#
# Ejemplo de request:
#   POST https://tuapp.railway.app/predecir
#   {"user_id": "001", "categoria": "Casa", "palabra": "quiero"}
#
# Ejemplo de response:
#   [
#     {"palabra": "comer",      "probabilidad": 45.2},
#     {"palabra": "dormir",     "probabilidad": 30.1},
#     {"palabra": "televisión", "probabilidad": 24.7}
#   ]

@app.post("/predecir")
def predecir(request: PredecirRequest):
    return predecir_top3(request.user_id, request.categoria, request.palabra)

# ── Endpoint 2: Reentrenar ────────────────────────────────────────────────────
# El back llama a este endpoint una vez por semana con todas las frases
# que usó el usuario desde la última actualización.
# Reentrena el modelo personalizado del usuario con esos datos.
#
# Ejemplo de request:
#   POST https://tuapp.railway.app/reentrenar
#   {
#     "user_id": "001",
#     "datos": [
#       {"categoria": "Casa",    "frase": ["quiero", "ver", "televisión"]},
#       {"categoria": "Escuela", "frase": ["necesito", "ayuda"]},
#       {"categoria": "Médico",  "frase": ["me", "duele", "cabeza"]}
#     ]
#   }
#
# Ejemplo de response:
#   {"status": "ok", "pares_entrenados": 5}

@app.post("/reentrenar")
def reentrenar_modelo(request: ReentrenarRequest):
    return reentrenar(request.user_id, request.datos)

# ── Endpoint 3: Health check ──────────────────────────────────────────────────
# Endpoint simple para verificar que la API está corriendo.
# Railway lo usa para saber si el servidor está vivo.
# También útil para que tu amiga pruebe que la conexión funciona.
#
# Ejemplo:
#   GET https://tuapp.railway.app/
#   → {"status": "ok"}

@app.get("/")
def health_check():
    return {"status": "ok"}
