import json
import os
import re

import numpy as np

# ── Rutas ──────────────────────────────────────────────────────────────────────
DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_NPZ  = os.path.join(DIR, "modelo_prediccion_lstm.npz")
RUTA_JSON = os.path.join(DIR, "modelo_prediccion_lstm.json")

# ── Dataset de prueba (500 casos) ──────────────────────────────────────────────
# Frases creadas manualmente, distintas al corpus de entrenamiento.
# Cada entrada tiene:
#   "contexto": últimas palabras escritas
#   "validas":  palabras que tendrían sentido como siguiente palabra
DATASET_PRUEBA = [
    # ── Deseos básicos (contexto 1 palabra) ──
    {"contexto": ["quiero"],               "validas": ["ir", "agua", "comer", "jugar", "dormir", "un", "una", "tomar"]},
    {"contexto": ["necesito"],             "validas": ["ir", "ayuda", "agua", "comer", "dormir", "un", "una"]},
    {"contexto": ["tengo"],                "validas": ["hambre", "sed", "frío", "calor", "miedo", "sueño", "ganas"]},
    {"contexto": ["estoy"],                "validas": ["bien", "mal", "cansado", "cansada", "contento", "contenta", "triste", "enfermo", "enferma"]},
    {"contexto": ["voy"],                  "validas": ["al", "a", "con", "para"]},
    {"contexto": ["hoy"],                  "validas": ["quiero", "tengo", "voy", "no", "me"]},
    {"contexto": ["mañana"],               "validas": ["voy", "quiero", "tengo", "no", "me"]},
    {"contexto": ["no"],                   "validas": ["quiero", "tengo", "puedo", "me", "voy", "sé"]},
    {"contexto": ["puedo"],                "validas": ["ir", "jugar", "comer", "dormir", "ver", "hacer"]},
    {"contexto": ["me"],                   "validas": ["duele", "gusta", "siento", "pica", "da"]},
    {"contexto": ["mi"],                   "validas": ["mamá", "papá", "hermano", "hermana", "abuela", "abuelo", "maestra", "perro"]},
    {"contexto": ["con"],                  "validas": ["mi", "mis", "el", "la", "los", "las"]},
    {"contexto": ["en"],                   "validas": ["el", "la", "mi", "casa"]},
    {"contexto": ["a"],                    "validas": ["la", "el", "mi", "casa", "comer", "jugar", "dormir"]},
    {"contexto": ["hay"],                  "validas": ["que", "un", "una", "mucho", "muchos"]},
    {"contexto": ["para"],                 "validas": ["mi", "el", "la", "los", "las", "ir", "comer"]},
    {"contexto": ["sin"],                  "validas": ["mi", "el", "la", "agua", "miedo"]},
    {"contexto": ["después"],              "validas": ["de", "quiero", "voy", "tengo"]},
    {"contexto": ["antes"],                "validas": ["de", "quiero", "voy", "tengo"]},
    {"contexto": ["también"],              "validas": ["quiero", "tengo", "voy", "me"]},

    # ── Deseos con 2 palabras de contexto ──
    {"contexto": ["quiero", "ir"],         "validas": ["al", "a", "con", "para"]},
    {"contexto": ["quiero", "comer"],      "validas": ["pizza", "arroz", "milanesa", "fideos", "un", "una", "algo"]},
    {"contexto": ["quiero", "tomar"],      "validas": ["agua", "jugo", "leche", "gaseosa", "un", "una"]},
    {"contexto": ["quiero", "jugar"],      "validas": ["con", "al", "en", "un"]},
    {"contexto": ["quiero", "ver"],        "validas": ["una", "un", "la", "el", "tele"]},
    {"contexto": ["quiero", "dormir"],     "validas": ["en", "con", "un", "mi", "la"]},
    {"contexto": ["quiero", "escuchar"],   "validas": ["música", "un", "una", "la"]},
    {"contexto": ["quiero", "leer"],       "validas": ["un", "una", "el", "la", "mi"]},
    {"contexto": ["quiero", "comprar"],    "validas": ["un", "una", "algo", "caramelos", "ropa"]},
    {"contexto": ["quiero", "bailar"],     "validas": ["con", "en", "un", "la"]},
    {"contexto": ["necesito", "ir"],       "validas": ["al", "a", "con"]},
    {"contexto": ["necesito", "ayuda"],    "validas": ["con", "para", "en"]},
    {"contexto": ["necesito", "dormir"],   "validas": ["en", "con", "un", "la"]},
    {"contexto": ["tengo", "hambre"],      "validas": ["quiero", "y", "pero", "porque"]},
    {"contexto": ["tengo", "sed"],         "validas": ["quiero", "y", "pero", "porque"]},
    {"contexto": ["tengo", "frío"],        "validas": ["quiero", "y", "pero", "porque"]},
    {"contexto": ["tengo", "miedo"],       "validas": ["porque", "de", "hoy", "y"]},
    {"contexto": ["tengo", "sueño"],       "validas": ["quiero", "y", "pero", "porque"]},
    {"contexto": ["tengo", "mucho"],       "validas": ["frío", "calor", "miedo", "sueño", "hambre"]},
    {"contexto": ["tengo", "mucha"],       "validas": ["sed", "hambre", "ganas", "tos"]},
    {"contexto": ["estoy", "bien"],        "validas": ["y", "pero", "hoy", "porque"]},
    {"contexto": ["estoy", "mal"],         "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "triste"],      "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "contento"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "muy"],         "validas": ["bien", "mal", "cansado", "cansada", "contento", "triste"]},
    {"contexto": ["estoy", "cansado"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["voy", "al"],            "validas": ["baño", "parque", "colegio", "médico", "club", "shopping"]},
    {"contexto": ["voy", "a"],             "validas": ["la", "comer", "dormir", "jugar", "ir"]},
    {"contexto": ["voy", "con"],           "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["no", "quiero"],         "validas": ["ir", "comer", "dormir", "jugar", "hacer"]},
    {"contexto": ["no", "puedo"],          "validas": ["ir", "comer", "dormir", "jugar", "hacer"]},
    {"contexto": ["no", "me"],             "validas": ["gusta", "duele", "siento", "pica"]},
    {"contexto": ["no", "tengo"],          "validas": ["hambre", "sed", "frío", "calor", "miedo", "ganas"]},
    {"contexto": ["me", "duele"],          "validas": ["la", "el", "mucho", "un"]},
    {"contexto": ["me", "gusta"],          "validas": ["la", "el", "mucho", "jugar", "comer"]},
    {"contexto": ["me", "pica"],           "validas": ["la", "el", "mucho", "un"]},
    {"contexto": ["mi", "mamá"],           "validas": ["quiere", "está", "va", "me", "tiene", "puede"]},
    {"contexto": ["mi", "papá"],           "validas": ["quiere", "está", "va", "me", "tiene", "puede"]},
    {"contexto": ["mi", "hermano"],        "validas": ["quiere", "está", "va", "me", "tiene", "puede"]},
    {"contexto": ["mi", "hermana"],        "validas": ["quiere", "está", "va", "me", "tiene", "puede"]},
    {"contexto": ["mi", "abuela"],         "validas": ["quiere", "está", "va", "me", "tiene", "puede"]},
    {"contexto": ["con", "mi"],            "validas": ["mamá", "papá", "hermano", "hermana", "abuela", "maestra", "amigo", "amiga"]},
    {"contexto": ["con", "mis"],           "validas": ["amigos", "amigos", "hermanos", "compañeros", "papás"]},
    {"contexto": ["en", "el"],             "validas": ["parque", "colegio", "baño", "living", "patio", "club"]},
    {"contexto": ["en", "la"],             "validas": ["escuela", "plaza", "casa", "pileta", "cocina", "cama"]},
    {"contexto": ["en", "mi"],             "validas": ["casa", "cuarto", "cama", "mochila"]},
    {"contexto": ["a", "la"],              "validas": ["noche", "tarde", "mañana", "escuela", "plaza", "casa"]},
    {"contexto": ["a", "la", "mañana"],    "validas": ["quiero", "tengo", "voy", "me", "como"]},
    {"contexto": ["a", "la", "tarde"],     "validas": ["quiero", "tengo", "voy", "me", "juego"]},
    {"contexto": ["a", "la", "noche"],     "validas": ["quiero", "tengo", "voy", "me", "duermo"]},
    {"contexto": ["hay", "que"],           "validas": ["ir", "comer", "dormir", "hacer", "comprar", "esperar"]},
    {"contexto": ["hoy", "quiero"],        "validas": ["ir", "jugar", "comer", "dormir", "ver"]},
    {"contexto": ["hoy", "tengo"],         "validas": ["hambre", "sed", "frío", "calor", "miedo", "sueño"]},
    {"contexto": ["hoy", "voy"],           "validas": ["al", "a", "con"]},
    {"contexto": ["hoy", "no"],            "validas": ["quiero", "puedo", "tengo", "voy"]},

    # ── Contexto de 3 palabras ──
    {"contexto": ["quiero", "ir", "al"],   "validas": ["parque", "baño", "colegio", "médico", "club"]},
    {"contexto": ["quiero", "ir", "a"],    "validas": ["la", "comer", "dormir", "jugar"]},
    {"contexto": ["quiero", "comer", "un"], "validas": ["sándwich", "helado", "yogur", "pancho"]},
    {"contexto": ["quiero", "comer", "una"], "validas": ["milanesa", "pizza", "galletita", "fruta"]},
    {"contexto": ["quiero", "tomar", "agua"], "validas": ["porque", "y", "con", "fría"]},
    {"contexto": ["quiero", "ver", "una"], "validas": ["película", "serie", "obra", "foto"]},
    {"contexto": ["voy", "al", "parque"],  "validas": ["con", "y", "porque", "hoy"]},
    {"contexto": ["voy", "a", "la"],       "validas": ["plaza", "escuela", "pileta", "casa", "cocina"]},
    {"contexto": ["voy", "con", "mi"],     "validas": ["mamá", "papá", "hermano", "amigo", "maestra"]},
    {"contexto": ["me", "duele", "la"],    "validas": ["cabeza", "panza", "garganta", "rodilla", "mano", "espalda"]},
    {"contexto": ["me", "duele", "el"],    "validas": ["estómago", "brazo", "pie", "codo", "diente", "oído"]},
    {"contexto": ["me", "gusta", "el"],    "validas": ["fútbol", "parque", "helado", "colegio", "juego"]},
    {"contexto": ["me", "gusta", "la"],    "validas": ["música", "pizza", "fruta", "tele", "escuela"]},
    {"contexto": ["no", "quiero", "ir"],   "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["no", "quiero", "comer"], "validas": ["más", "eso", "pizza", "verdura"]},
    {"contexto": ["mi", "mamá", "quiere"], "validas": ["ir", "comer", "comprar", "que", "hacer"]},
    {"contexto": ["mi", "papá", "tiene"],  "validas": ["hambre", "sed", "frío", "calor", "miedo"]},
    {"contexto": ["estoy", "muy", "bien"], "validas": ["porque", "hoy", "y", "gracias"]},
    {"contexto": ["estoy", "muy", "mal"],  "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["tengo", "mucho", "frío"], "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["tengo", "mucha", "sed"], "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["hoy", "quiero", "ir"],  "validas": ["al", "a", "con"]},
    {"contexto": ["hoy", "no", "quiero"],  "validas": ["ir", "comer", "hacer", "jugar"]},
    {"contexto": ["en", "el", "parque"],   "validas": ["quiero", "con", "hay", "juego"]},
    {"contexto": ["en", "la", "escuela"],  "validas": ["quiero", "tengo", "hay", "me"]},

    # ── Dolor y salud ──
    {"contexto": ["me", "duele", "mucho"], "validas": ["la", "el", "un", "todo"]},
    {"contexto": ["me", "pica", "la"],     "validas": ["cabeza", "espalda", "panza", "mano", "oreja"]},
    {"contexto": ["me", "pica", "el"],     "validas": ["brazo", "cuello", "ojo", "codo"]},
    {"contexto": ["tengo", "fiebre"],      "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["tengo", "tos"],         "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["estoy", "enfermo"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "enferma"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["me", "siento"],         "validas": ["bien", "mal", "cansado", "triste", "contento"]},
    {"contexto": ["me", "siento", "mal"],  "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["voy", "al", "médico"],  "validas": ["porque", "con", "hoy", "mañana"]},

    # ── Emociones ──
    {"contexto": ["estoy", "feliz"],       "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "enojado"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "enojada"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "asustado"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "asustada"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "aburrido"],    "validas": ["porque", "hoy", "y", "pero", "quiero"]},
    {"contexto": ["estoy", "aburrida"],    "validas": ["porque", "hoy", "y", "pero", "quiero"]},
    {"contexto": ["tengo", "ganas"],       "validas": ["de", "pero", "y"]},
    {"contexto": ["tengo", "ganas", "de"], "validas": ["ir", "jugar", "comer", "dormir", "ver"]},
    {"contexto": ["no", "tengo", "ganas"], "validas": ["de", "pero", "y"]},

    # ── Acciones cotidianas ──
    {"contexto": ["voy", "a", "comer"],    "validas": ["con", "en", "un", "una", "algo"]},
    {"contexto": ["voy", "a", "dormir"],   "validas": ["con", "en", "un", "porque"]},
    {"contexto": ["voy", "a", "jugar"],    "validas": ["con", "al", "en", "un"]},
    {"contexto": ["voy", "a", "bañarme"],  "validas": ["porque", "con", "y", "hoy"]},
    {"contexto": ["tengo", "que"],         "validas": ["ir", "comer", "dormir", "hacer", "lavarme"]},
    {"contexto": ["tengo", "que", "ir"],   "validas": ["al", "a", "con"]},
    {"contexto": ["voy", "a", "lavarme"],  "validas": ["los", "las", "el", "la"]},
    {"contexto": ["quiero", "cambiarme"],  "validas": ["de", "porque", "hoy", "y"]},
    {"contexto": ["quiero", "bañarme"],    "validas": ["porque", "con", "y", "hoy"]},
    {"contexto": ["quiero", "descansar"],  "validas": ["en", "con", "un", "porque"]},

    # ── Comidas y bebidas ──
    {"contexto": ["quiero", "comer", "pizza"], "validas": ["con", "y", "porque", "hoy"]},
    {"contexto": ["quiero", "comer", "arroz"], "validas": ["con", "y", "porque", "hoy"]},
    {"contexto": ["quiero", "tomar", "leche"], "validas": ["con", "y", "porque", "fría"]},
    {"contexto": ["quiero", "tomar", "jugo"],  "validas": ["de", "con", "y", "porque"]},
    {"contexto": ["quiero", "un"],         "validas": ["helado", "jugo", "sándwich", "vaso", "pancho"]},
    {"contexto": ["quiero", "una"],        "validas": ["pizza", "milanesa", "galletita", "fruta", "manzana"]},
    {"contexto": ["quiero", "más"],        "validas": ["agua", "leche", "jugo", "comida", "arroz"]},
    {"contexto": ["no", "quiero", "más"],  "validas": ["agua", "comida", "eso", "hacer"]},
    {"contexto": ["me", "gusta", "mucho"], "validas": ["la", "el", "jugar", "comer", "bailar"]},
    {"contexto": ["no", "me", "gusta"],    "validas": ["la", "el", "eso", "hacer", "comer"]},

    # ── Lugar y destino ──
    {"contexto": ["voy", "al", "baño"],    "validas": ["porque", "con", "y", "hoy"]},
    {"contexto": ["voy", "al", "parque"],  "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["voy", "a", "la", "escuela"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["estoy", "en"],          "validas": ["el", "la", "mi", "casa"]},
    {"contexto": ["estoy", "en", "el"],    "validas": ["parque", "baño", "colegio", "living", "patio"]},
    {"contexto": ["estoy", "en", "la"],    "validas": ["escuela", "plaza", "casa", "cocina", "cama"]},
    {"contexto": ["voy", "al", "colegio"], "validas": ["con", "porque", "y", "hoy", "mañana"]},
    {"contexto": ["voy", "a", "la", "plaza"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["quiero", "ir", "al", "parque"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["quiero", "ir", "a", "la"], "validas": ["plaza", "escuela", "pileta", "casa"]},

    # ── Familia ──
    {"contexto": ["mi", "mamá", "está"],   "validas": ["bien", "mal", "en", "con", "aquí"]},
    {"contexto": ["mi", "papá", "va"],     "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["mi", "hermano", "quiere"], "validas": ["ir", "comer", "jugar", "hacer"]},
    {"contexto": ["mi", "abuela", "tiene"], "validas": ["hambre", "sed", "frío", "calor", "miedo"]},
    {"contexto": ["con", "mi", "mamá"],    "validas": ["quiero", "voy", "estoy", "porque"]},
    {"contexto": ["con", "mi", "papá"],    "validas": ["quiero", "voy", "estoy", "porque"]},
    {"contexto": ["con", "mis", "amigos"], "validas": ["quiero", "voy", "estoy", "juego"]},
    {"contexto": ["con", "mi", "hermano"], "validas": ["quiero", "voy", "estoy", "juego"]},
    {"contexto": ["mi", "perro"],          "validas": ["quiere", "está", "tiene", "se"]},
    {"contexto": ["mi", "perro", "tiene"], "validas": ["hambre", "sed", "frío", "calor", "miedo"]},

    # ── Tiempo y frecuencia ──
    {"contexto": ["siempre"],              "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["nunca"],                "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["a", "veces"],           "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["todos", "los"],         "validas": ["días", "fines"]},
    {"contexto": ["todos", "los", "días"], "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["el", "fin"],            "validas": ["de"]},
    {"contexto": ["el", "fin", "de"],      "validas": ["semana"]},
    {"contexto": ["esta"],                 "validas": ["tarde", "noche", "mañana", "semana"]},
    {"contexto": ["esta", "tarde"],        "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["esta", "noche"],        "validas": ["quiero", "tengo", "voy", "me"]},

    # ── Pedir y agradecer ──
    {"contexto": ["por", "favor"],         "validas": ["quiero", "necesito", "dame", "ayuda"]},
    {"contexto": ["gracias"],              "validas": ["por", "quiero", "y", "porque"]},
    {"contexto": ["perdón"],               "validas": ["por", "quiero", "y", "porque"]},
    {"contexto": ["ayuda"],                "validas": ["con", "por", "para", "quiero"]},
    {"contexto": ["dame"],                 "validas": ["agua", "un", "una", "más", "la", "el"]},
    {"contexto": ["dame", "más"],          "validas": ["agua", "leche", "jugo", "comida"]},
    {"contexto": ["quiero", "pedir"],      "validas": ["ayuda", "un", "una", "permiso"]},
    {"contexto": ["quiero", "hablar"],     "validas": ["con", "de", "porque"]},
    {"contexto": ["quiero", "hablar", "con"], "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["no", "entiendo"],       "validas": ["la", "el", "eso", "porque", "nada"]},

    # ── Actividades ──
    {"contexto": ["quiero", "pintar"],     "validas": ["un", "una", "con", "en"]},
    {"contexto": ["quiero", "dibujar"],    "validas": ["un", "una", "con", "en"]},
    {"contexto": ["quiero", "armar"],      "validas": ["un", "una", "con", "en"]},
    {"contexto": ["quiero", "cantar"],     "validas": ["un", "una", "con", "en", "porque"]},
    {"contexto": ["quiero", "bailar"],     "validas": ["con", "en", "un", "la"]},
    {"contexto": ["quiero", "correr"],     "validas": ["en", "con", "al", "porque"]},
    {"contexto": ["quiero", "nadar"],      "validas": ["en", "con", "porque", "hoy"]},
    {"contexto": ["quiero", "andar"],      "validas": ["en", "a", "con"]},
    {"contexto": ["quiero", "andar", "en"], "validas": ["bici", "auto", "moto"]},
    {"contexto": ["quiero", "mirar"],      "validas": ["la", "el", "un", "una", "tele"]},

    # ── Ropa y objetos ──
    {"contexto": ["quiero", "ponerme"],    "validas": ["el", "la", "un", "una", "los"]},
    {"contexto": ["quiero", "sacarme"],    "validas": ["el", "la", "un", "una", "los"]},
    {"contexto": ["quiero", "buscar"],     "validas": ["mi", "mis", "el", "la", "un", "una"]},
    {"contexto": ["quiero", "buscar", "mi"], "validas": ["mochila", "ropa", "juguete", "pelota"]},
    {"contexto": ["perdí"],                "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["perdí", "mi"],          "validas": ["mochila", "ropa", "juguete", "pelota", "libro"]},
    {"contexto": ["encontré"],             "validas": ["mi", "mis", "el", "la", "un", "una"]},
    {"contexto": ["tengo", "mi"],          "validas": ["mochila", "ropa", "libro", "pelota"]},
    {"contexto": ["no", "encuentro"],      "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["no", "encuentro", "mi"], "validas": ["mochila", "ropa", "libro", "pelota"]},

    # ── Clima ──
    {"contexto": ["hace"],                 "validas": ["frío", "calor", "mucho", "poco", "viento", "sol"]},
    {"contexto": ["hace", "mucho"],        "validas": ["frío", "calor", "viento", "sol"]},
    {"contexto": ["hace", "frío"],         "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["hace", "calor"],        "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["está", "lloviendo"],    "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["hay", "sol"],           "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["hay", "viento"],        "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["el", "clima"],          "validas": ["está", "es", "hace"]},

    # ── Preguntas y negaciones ──
    {"contexto": ["no", "sé"],             "validas": ["cómo", "qué", "dónde", "cuándo", "por"]},
    {"contexto": ["no", "sé", "cómo"],     "validas": ["ir", "hacer", "jugar", "comer"]},
    {"contexto": ["no", "entiendo"],       "validas": ["la", "el", "eso", "porque", "nada"]},
    {"contexto": ["no", "puedo"],          "validas": ["ir", "comer", "dormir", "jugar", "hacer"]},
    {"contexto": ["no", "puedo", "ir"],    "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["tampoco"],              "validas": ["quiero", "puedo", "tengo", "voy"]},
    {"contexto": ["solo"],                 "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["ya"],                   "validas": ["quiero", "tengo", "voy", "me", "sé"]},
    {"contexto": ["todavía"],              "validas": ["quiero", "tengo", "no", "me"]},
    {"contexto": ["más"],                  "validas": ["agua", "comida", "tarde", "o", "y"]},

    # ── Conjunciones y conectores ──
    {"contexto": ["porque"],               "validas": ["quiero", "tengo", "no", "me", "voy"]},
    {"contexto": ["pero"],                 "validas": ["quiero", "tengo", "no", "me", "voy"]},
    {"contexto": ["y"],                    "validas": ["quiero", "tengo", "no", "me", "voy"]},
    {"contexto": ["después", "de"],        "validas": ["comer", "dormir", "jugar", "ir", "la"]},
    {"contexto": ["antes", "de"],          "validas": ["comer", "dormir", "jugar", "ir", "la"]},
    {"contexto": ["cuando"],               "validas": ["quiero", "tengo", "voy", "me", "no"]},

    # ── Variantes de persona ──
    {"contexto": ["él"],                   "validas": ["quiere", "tiene", "va", "está", "puede"]},
    {"contexto": ["ella"],                 "validas": ["quiere", "tiene", "va", "está", "puede"]},
    {"contexto": ["ellos"],                "validas": ["quieren", "tienen", "van", "están", "pueden"]},
    {"contexto": ["ellas"],                "validas": ["quieren", "tienen", "van", "están", "pueden"]},
    {"contexto": ["nosotros"],             "validas": ["queremos", "tenemos", "vamos", "estamos", "podemos"]},
    {"contexto": ["yo"],                   "validas": ["quiero", "tengo", "voy", "estoy", "puedo"]},
    {"contexto": ["vos"],                  "validas": ["querés", "tenés", "vas", "estás", "podés"]},
    {"contexto": ["él", "quiere"],         "validas": ["ir", "comer", "jugar", "dormir"]},
    {"contexto": ["ella", "tiene"],        "validas": ["hambre", "sed", "frío", "calor", "miedo"]},
    {"contexto": ["ellos", "van"],         "validas": ["al", "a", "con"]},

    # ── Variantes de artículo ──
    {"contexto": ["el"],                   "validas": ["parque", "baño", "colegio", "médico", "club"]},
    {"contexto": ["la"],                   "validas": ["escuela", "plaza", "casa", "pileta", "cocina"]},
    {"contexto": ["un"],                   "validas": ["helado", "sándwich", "jugo", "vaso", "libro"]},
    {"contexto": ["una"],                  "validas": ["pizza", "milanesa", "galletita", "fruta", "manzana"]},
    {"contexto": ["los"],                  "validas": ["días", "fines", "amigos", "juguetes"]},
    {"contexto": ["las"],                  "validas": ["noches", "tardes", "mañanas", "amigas"]},

    # ── Colores y descripciones ──
    {"contexto": ["quiero", "el"],         "validas": ["rojo", "azul", "verde", "amarillo", "libro", "juego"]},
    {"contexto": ["quiero", "la"],         "validas": ["roja", "azul", "verde", "pelota", "mochila"]},
    {"contexto": ["es"],                   "validas": ["mi", "el", "la", "un", "una", "muy"]},
    {"contexto": ["es", "muy"],            "validas": ["grande", "chico", "bueno", "lindo", "rico"]},

    # ── Escuela ──
    {"contexto": ["en", "la", "escuela"],  "validas": ["quiero", "tengo", "hay", "me"]},
    {"contexto": ["la", "maestra"],        "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mis", "compañeros"],    "validas": ["quieren", "tienen", "van", "están"]},
    {"contexto": ["tengo", "tarea"],       "validas": ["porque", "y", "pero", "para"]},
    {"contexto": ["mañana", "tengo"],      "validas": ["tarea", "hambre", "sed", "frío", "colegio"]},
    {"contexto": ["mañana", "voy"],        "validas": ["al", "a", "con"]},
    {"contexto": ["hoy", "en"],            "validas": ["el", "la", "mi"]},
    {"contexto": ["hoy", "en", "la"],      "validas": ["escuela", "plaza", "casa", "tarde"]},

    # ── Casa y rutinas ──
    {"contexto": ["en", "casa"],           "validas": ["quiero", "tengo", "hay", "me"]},
    {"contexto": ["quiero", "ir", "a", "casa"], "validas": ["porque", "con", "y", "hoy"]},
    {"contexto": ["estoy", "en", "casa"],  "validas": ["porque", "y", "con", "hoy"]},
    {"contexto": ["voy", "a", "casa"],     "validas": ["porque", "con", "y", "hoy"]},
    {"contexto": ["quiero", "poner"],      "validas": ["la", "el", "los", "música", "tele"]},
    {"contexto": ["quiero", "prender"],    "validas": ["la", "el", "los", "tele", "luz"]},
    {"contexto": ["quiero", "apagar"],     "validas": ["la", "el", "los", "tele", "luz"]},
    {"contexto": ["quiero", "abrir"],      "validas": ["la", "el", "los", "ventana", "puerta"]},
    {"contexto": ["quiero", "cerrar"],     "validas": ["la", "el", "los", "ventana", "puerta"]},
    {"contexto": ["quiero", "ordenar"],    "validas": ["mi", "mis", "el", "la", "los"]},

    # ── Variantes de "quiero" ──
    {"contexto": ["quisiera"],             "validas": ["ir", "comer", "jugar", "dormir", "un", "una"]},
    {"contexto": ["me", "gustaría"],       "validas": ["ir", "comer", "jugar", "dormir", "un", "una"]},
    {"contexto": ["podría"],               "validas": ["ir", "comer", "jugar", "dormir", "un", "una"]},
    {"contexto": ["debería"],              "validas": ["ir", "comer", "dormir", "hacer", "lavarme"]},

    # ── Expresiones ──
    {"contexto": ["qué"],                  "validas": ["rico", "bueno", "lindo", "pasa", "quiero"]},
    {"contexto": ["cómo"],                 "validas": ["estás", "estoy", "se", "quiero"]},
    {"contexto": ["dónde"],                "validas": ["está", "estoy", "voy", "quiero"]},
    {"contexto": ["cuándo"],               "validas": ["vamos", "voy", "comes", "podemos"]},
    {"contexto": ["mucho"],                "validas": ["mejor", "más", "frío", "calor", "miedo"]},
    {"contexto": ["poco"],                 "validas": ["más", "a", "de", "mejor"]},
    {"contexto": ["muy"],                  "validas": ["bien", "mal", "grande", "chico", "bueno"]},
    {"contexto": ["bastante"],             "validas": ["bien", "mal", "grande", "cansado", "mejor"]},

    # ── Mixtos y variados ──
    {"contexto": ["quiero", "ir", "con"],  "validas": ["mi", "mis", "el", "la", "vos"]},
    {"contexto": ["voy", "a", "dormir"],   "validas": ["con", "en", "un", "porque"]},
    {"contexto": ["mañana", "quiero"],     "validas": ["ir", "jugar", "comer", "dormir", "ver"]},
    {"contexto": ["no", "me", "gusta"],    "validas": ["la", "el", "eso", "hacer", "comer"]},
    {"contexto": ["me", "gusta", "mucho"], "validas": ["la", "el", "jugar", "comer", "bailar"]},
    {"contexto": ["tengo", "que", "ir"],   "validas": ["al", "a", "con"]},
    {"contexto": ["voy", "a", "mirar"],    "validas": ["la", "el", "un", "una", "tele"]},
    {"contexto": ["quiero", "más"],        "validas": ["agua", "leche", "jugo", "comida", "arroz"]},
    {"contexto": ["no", "quiero", "más"],  "validas": ["agua", "comida", "eso", "hacer"]},
    {"contexto": ["hace", "mucho", "frío"], "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["hace", "mucho", "calor"], "validas": ["quiero", "y", "porque", "pero"]},
    {"contexto": ["estoy", "bien", "gracias"], "validas": ["y", "pero", "porque", "quiero"]},
    {"contexto": ["quiero", "quedarme"],   "validas": ["en", "con", "aquí", "porque"]},
    {"contexto": ["quiero", "irme"],       "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["no", "quiero", "ir"],   "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["voy", "a", "buscar"],   "validas": ["mi", "mis", "el", "la", "un"]},
    {"contexto": ["quiero", "llamar"],     "validas": ["a", "mi", "al", "porque"]},
    {"contexto": ["quiero", "llamar", "a"], "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["quiero", "llamar", "a", "mi"], "validas": ["mamá", "papá", "abuela", "maestra"]},
    {"contexto": ["quiero", "ir", "al", "baño"], "validas": ["porque", "ya", "ahora", "por"]},
    {"contexto": ["tengo", "que", "lavarme"], "validas": ["los", "las", "el", "la"]},
    {"contexto": ["quiero", "lavarme"],    "validas": ["los", "las", "el", "la"]},
    {"contexto": ["quiero", "lavarme", "los"], "validas": ["dientes", "manos", "pies"]},
    {"contexto": ["voy", "al", "médico", "porque"], "validas": ["tengo", "me", "no", "estoy"]},
    {"contexto": ["mañana", "no"],         "validas": ["quiero", "puedo", "tengo", "voy"]},
    {"contexto": ["el", "lunes"],          "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "martes"],         "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["este", "fin"],          "validas": ["de"]},
    {"contexto": ["este", "fin", "de"],    "validas": ["semana"]},
    {"contexto": ["esta", "semana"],       "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "próximo"],        "validas": ["lunes", "martes", "fin", "año"]},

    # ── Más deseos y necesidades ──
    {"contexto": ["quiero", "salir"],       "validas": ["a", "con", "al", "porque"]},
    {"contexto": ["quiero", "entrar"],      "validas": ["a", "al", "en", "porque"]},
    {"contexto": ["quiero", "subir"],       "validas": ["al", "a", "las", "los"]},
    {"contexto": ["quiero", "bajar"],       "validas": ["al", "a", "las", "los"]},
    {"contexto": ["quiero", "sentarme"],    "validas": ["en", "con", "al", "aquí"]},
    {"contexto": ["quiero", "pararme"],     "validas": ["en", "aquí", "porque", "y"]},
    {"contexto": ["quiero", "acostarme"],   "validas": ["en", "con", "porque", "ya"]},
    {"contexto": ["quiero", "levantarme"],  "validas": ["ya", "porque", "y", "hoy"]},
    {"contexto": ["quiero", "quedarme"],    "validas": ["en", "con", "aquí", "porque"]},
    {"contexto": ["quiero", "irme"],        "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["necesito", "hablar"],    "validas": ["con", "de", "porque"]},
    {"contexto": ["necesito", "descansar"], "validas": ["en", "con", "porque", "ya"]},
    {"contexto": ["necesito", "lavarme"],   "validas": ["los", "las", "el", "la"]},
    {"contexto": ["necesito", "cambiarme"], "validas": ["de", "porque", "ya", "y"]},
    {"contexto": ["necesito", "comer"],     "validas": ["algo", "un", "una", "porque"]},

    # ── Más emociones y estados ──
    {"contexto": ["estoy", "nervioso"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "nerviosa"],     "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "tranquilo"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "tranquila"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "emocionado"],   "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "emocionada"],   "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "frustrado"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["estoy", "frustrada"],    "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["me", "siento", "bien"],  "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["me", "siento", "triste"], "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["me", "alegra"],          "validas": ["que", "mucho", "ir", "ver"]},
    {"contexto": ["me", "preocupa"],        "validas": ["que", "mucho", "porque"]},
    {"contexto": ["me", "aburre"],          "validas": ["esto", "que", "mucho", "porque"]},
    {"contexto": ["me", "encanta"],         "validas": ["la", "el", "jugar", "comer", "bailar"]},
    {"contexto": ["me", "molesta"],         "validas": ["que", "mucho", "esto", "cuando"]},

    # ── Más rutinas y acciones ──
    {"contexto": ["voy", "a", "estudiar"],  "validas": ["con", "en", "porque", "hoy"]},
    {"contexto": ["voy", "a", "trabajar"],  "validas": ["con", "en", "porque", "hoy"]},
    {"contexto": ["voy", "a", "cocinar"],   "validas": ["con", "en", "porque", "algo"]},
    {"contexto": ["voy", "a", "limpiar"],   "validas": ["la", "el", "mi", "porque"]},
    {"contexto": ["voy", "a", "comprar"],   "validas": ["un", "una", "algo", "porque"]},
    {"contexto": ["tengo", "que", "estudiar"], "validas": ["porque", "hoy", "mañana", "para"]},
    {"contexto": ["tengo", "que", "comer"], "validas": ["algo", "un", "una", "porque"]},
    {"contexto": ["tengo", "que", "dormir"], "validas": ["porque", "ya", "hoy", "en"]},
    {"contexto": ["tengo", "que", "lavarme"], "validas": ["los", "las", "el", "la"]},
    {"contexto": ["tengo", "que", "hacer"], "validas": ["la", "el", "mi", "algo", "tarea"]},

    # ── Más lugares ──
    {"contexto": ["voy", "al", "club"],     "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["voy", "al", "shopping"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["voy", "a", "la", "pileta"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["voy", "a", "la", "cocina"], "validas": ["porque", "a", "con", "y"]},
    {"contexto": ["estoy", "en", "mi"],     "validas": ["casa", "cuarto", "cama", "mochila"]},
    {"contexto": ["estoy", "en", "el", "parque"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["estoy", "en", "la", "escuela"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["quiero", "ir", "a", "la", "pileta"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["quiero", "ir", "al", "club"], "validas": ["con", "porque", "y", "hoy"]},
    {"contexto": ["quiero", "ir", "a", "casa"], "validas": ["porque", "con", "ya", "hoy"]},

    # ── Más familia y personas ──
    {"contexto": ["mi", "tío"],             "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mi", "tía"],             "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mi", "primo"],           "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mi", "prima"],           "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mi", "amigo"],           "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mi", "amiga"],           "validas": ["quiere", "está", "va", "me", "tiene"]},
    {"contexto": ["mis", "amigos"],         "validas": ["quieren", "están", "van", "me", "tienen"]},
    {"contexto": ["mis", "padres"],         "validas": ["quieren", "están", "van", "me", "tienen"]},
    {"contexto": ["con", "mi", "amigo"],    "validas": ["quiero", "voy", "estoy", "juego"]},
    {"contexto": ["con", "mi", "abuela"],   "validas": ["quiero", "voy", "estoy", "porque"]},

    # ── Más comidas ──
    {"contexto": ["quiero", "comer", "fideos"], "validas": ["con", "y", "porque", "hoy"]},
    {"contexto": ["quiero", "comer", "ensalada"], "validas": ["con", "y", "porque", "hoy"]},
    {"contexto": ["quiero", "comer", "fruta"], "validas": ["con", "y", "porque", "hoy"]},
    {"contexto": ["quiero", "tomar", "gaseosa"], "validas": ["con", "y", "porque", "fría"]},
    {"contexto": ["quiero", "tomar", "té"], "validas": ["con", "y", "porque", "caliente"]},
    {"contexto": ["quiero", "un", "helado"], "validas": ["de", "con", "y", "porque"]},
    {"contexto": ["quiero", "una", "pizza"], "validas": ["con", "de", "y", "porque"]},
    {"contexto": ["quiero", "una", "fruta"], "validas": ["con", "de", "y", "porque"]},
    {"contexto": ["tengo", "hambre", "y"],  "validas": ["quiero", "necesito", "voy", "tengo"]},
    {"contexto": ["tengo", "sed", "y"],     "validas": ["quiero", "necesito", "voy", "tengo"]},

    # ── Más salud ──
    {"contexto": ["me", "duele", "mucho", "la"], "validas": ["cabeza", "panza", "garganta", "rodilla"]},
    {"contexto": ["me", "duele", "mucho", "el"], "validas": ["estómago", "brazo", "pie", "codo"]},
    {"contexto": ["tengo", "dolor"],        "validas": ["de", "en", "mucho", "porque"]},
    {"contexto": ["tengo", "dolor", "de"],  "validas": ["cabeza", "panza", "garganta", "espalda"]},
    {"contexto": ["me", "siento", "enfermo"], "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["me", "siento", "enferma"], "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["voy", "al", "médico", "con"], "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["el", "médico", "dice"],  "validas": ["que", "mi", "porque"]},
    {"contexto": ["tengo", "que", "tomar"], "validas": ["el", "la", "un", "agua", "medicamento"]},
    {"contexto": ["me", "tomé"],            "validas": ["el", "la", "un", "una"]},

    # ── Expresiones más complejas ──
    {"contexto": ["quiero", "que"],         "validas": ["mi", "vos", "él", "ella", "nos"]},
    {"contexto": ["espero", "que"],         "validas": ["mi", "vos", "él", "ella", "podamos"]},
    {"contexto": ["creo", "que"],           "validas": ["voy", "tengo", "no", "mi"]},
    {"contexto": ["sé", "que"],             "validas": ["voy", "tengo", "no", "mi", "puedo"]},
    {"contexto": ["pienso", "que"],         "validas": ["voy", "tengo", "no", "mi"]},
    {"contexto": ["me", "parece", "que"],   "validas": ["voy", "tengo", "no", "mi"]},
    {"contexto": ["ojalá"],                 "validas": ["que", "pueda", "podamos", "venga"]},
    {"contexto": ["capaz"],                 "validas": ["que", "voy", "pueda", "mañana"]},
    {"contexto": ["tal", "vez"],            "validas": ["voy", "pueda", "mañana", "hoy"]},
    {"contexto": ["de", "repente"],         "validas": ["quiero", "tengo", "me", "no"]},

    # ── Más conectores y estructura ──
    {"contexto": ["primero"],               "validas": ["quiero", "tengo", "voy", "me"]},
    {"contexto": ["después", "de", "comer"], "validas": ["quiero", "voy", "tengo", "me"]},
    {"contexto": ["antes", "de", "dormir"], "validas": ["quiero", "voy", "tengo", "me"]},
    {"contexto": ["mientras"],              "validas": ["quiero", "tengo", "voy", "como", "juego"]},
    {"contexto": ["aunque"],               "validas": ["quiero", "tengo", "no", "me"]},
    {"contexto": ["si"],                    "validas": ["quiero", "tengo", "no", "me", "voy"]},
    {"contexto": ["si", "quiero"],          "validas": ["ir", "comer", "jugar", "dormir"]},
    {"contexto": ["cuando", "quiero"],      "validas": ["ir", "comer", "jugar", "dormir"]},
    {"contexto": ["para", "que"],           "validas": ["pueda", "podamos", "quiero", "tengo"]},
    {"contexto": ["para", "ir"],            "validas": ["al", "a", "con"]},

    # ── Días de la semana ──
    {"contexto": ["el", "domingo"],         "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "sábado"],          "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "viernes"],         "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "jueves"],          "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "miércoles"],       "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "domingo", "quiero"], "validas": ["ir", "jugar", "comer", "dormir", "ver"]},
    {"contexto": ["el", "sábado", "voy"],   "validas": ["al", "a", "con"]},
    {"contexto": ["mañana", "es"],          "validas": ["mi", "el", "la", "un", "lunes"]},
    {"contexto": ["hoy", "es"],             "validas": ["mi", "el", "la", "un", "lunes"]},
    {"contexto": ["pasado", "mañana"],      "validas": ["voy", "quiero", "tengo", "no"]},

    # ── Más variantes ──
    {"contexto": ["ayer"],                  "validas": ["fui", "quise", "tenía", "me", "no"]},
    {"contexto": ["ayer", "fui"],           "validas": ["al", "a", "con"]},
    {"contexto": ["ayer", "me"],            "validas": ["dolió", "gustó", "puse", "fui"]},
    {"contexto": ["la", "semana"],          "validas": ["que", "pasada", "próxima"]},
    {"contexto": ["la", "semana", "pasada"], "validas": ["fui", "quise", "tenía", "me"]},
    {"contexto": ["el", "mes"],             "validas": ["que", "pasado", "próximo", "de"]},
    {"contexto": ["este", "año"],           "validas": ["quiero", "tengo", "voy", "no"]},
    {"contexto": ["el", "año"],             "validas": ["que", "pasado", "próximo", "nuevo"]},
    {"contexto": ["hace", "poco"],          "validas": ["quiero", "tenía", "me", "fui"]},
    {"contexto": ["hace", "mucho", "tiempo"], "validas": ["quiero", "tenía", "me", "fui"]},

    # ── Expresiones de acuerdo y desacuerdo ──
    {"contexto": ["sí", "quiero"],          "validas": ["ir", "comer", "jugar", "dormir"]},
    {"contexto": ["sí", "tengo"],           "validas": ["hambre", "sed", "frío", "calor"]},
    {"contexto": ["no", "sé", "si"],        "validas": ["quiero", "puedo", "tengo", "voy"]},
    {"contexto": ["está", "bien"],          "validas": ["que", "porque", "y", "pero"]},
    {"contexto": ["está", "mal"],           "validas": ["que", "porque", "y", "pero"]},
    {"contexto": ["me", "parece", "bien"],  "validas": ["que", "porque", "y", "ir"]},
    {"contexto": ["me", "parece", "mal"],   "validas": ["que", "porque", "y", "pero"]},
    {"contexto": ["de", "acuerdo"],         "validas": ["quiero", "voy", "con", "y"]},
    {"contexto": ["no", "está", "bien"],    "validas": ["que", "porque", "y", "eso"]},
    {"contexto": ["qué", "bien"],           "validas": ["que", "porque", "y", "quiero"]},

    # ── Más con mi / mis ──
    {"contexto": ["mis", "hermanos"],       "validas": ["quieren", "están", "van", "me"]},
    {"contexto": ["mis", "hermanas"],       "validas": ["quieren", "están", "van", "me"]},
    {"contexto": ["mis", "primos"],         "validas": ["quieren", "están", "van", "me"]},
    {"contexto": ["mis", "tíos"],           "validas": ["quieren", "están", "van", "me"]},
    {"contexto": ["mis", "abuelos"],        "validas": ["quieren", "están", "van", "me"]},
    {"contexto": ["con", "mis", "hermanos"], "validas": ["quiero", "voy", "estoy", "juego"]},
    {"contexto": ["con", "mis", "amigos"],  "validas": ["quiero", "voy", "estoy", "juego"]},
    {"contexto": ["con", "mis", "primos"],  "validas": ["quiero", "voy", "estoy", "juego"]},
    {"contexto": ["mi", "casa"],            "validas": ["está", "es", "queda", "tiene"]},
    {"contexto": ["mi", "cuarto"],          "validas": ["está", "es", "tiene", "queda"]},

    # ── Más complejos ──
    {"contexto": ["quiero", "ir", "al", "médico"], "validas": ["porque", "con", "ya", "hoy"]},
    {"contexto": ["tengo", "que", "ir", "al"], "validas": ["baño", "colegio", "médico", "club"]},
    {"contexto": ["no", "quiero", "ir", "al"], "validas": ["colegio", "médico", "baño", "club"]},
    {"contexto": ["voy", "a", "la", "pileta", "con"], "validas": ["mi", "mis", "el", "la"]},
    {"contexto": ["mañana", "voy", "al"],   "validas": ["colegio", "médico", "club", "parque"]},
    {"contexto": ["hoy", "voy", "al"],      "validas": ["colegio", "médico", "club", "parque"]},
    {"contexto": ["el", "domingo", "voy"],  "validas": ["al", "a", "con"]},
    {"contexto": ["el", "sábado", "quiero"], "validas": ["ir", "jugar", "comer", "dormir"]},
    {"contexto": ["mañana", "tengo", "que"], "validas": ["ir", "comer", "dormir", "hacer"]},
    {"contexto": ["hoy", "tengo", "que"],   "validas": ["ir", "comer", "dormir", "hacer"]},

    # ── Últimos 40 casos ──
    {"contexto": ["quiero", "más"],         "validas": ["agua", "comida", "tiempo", "jugo"]},
    {"contexto": ["quiero", "menos"],       "validas": ["ruido", "trabajo", "tiempo"]},
    {"contexto": ["hace", "calor"],         "validas": ["hoy", "afuera", "y", "porque"]},
    {"contexto": ["hace", "frío"],          "validas": ["hoy", "afuera", "y", "porque"]},
    {"contexto": ["está", "nublado"],       "validas": ["hoy", "afuera", "y", "porque"]},
    {"contexto": ["el", "clima"],           "validas": ["está", "es", "hoy", "afuera"]},
    {"contexto": ["afuera"],                "validas": ["hace", "está", "quiero", "hay"]},
    {"contexto": ["adentro"],               "validas": ["está", "hace", "quiero", "hay"]},
    {"contexto": ["voy", "a", "quedarme"],  "validas": ["en", "con", "aquí", "porque"]},
    {"contexto": ["no", "quiero", "salir"], "validas": ["porque", "hoy", "y", "pero"]},
    {"contexto": ["no", "puedo"],           "validas": ["ir", "comer", "dormir", "hablar"]},
    {"contexto": ["no", "tengo", "ganas"],  "validas": ["de", "porque", "hoy", "y"]},
    {"contexto": ["tengo", "ganas", "de"],  "validas": ["ir", "comer", "jugar", "dormir"]},
    {"contexto": ["me", "gustan", "los"],   "validas": ["animales", "deportes", "juegos"]},
    {"contexto": ["me", "gustan", "las"],   "validas": ["frutas", "verduras", "películas"]},
    {"contexto": ["me", "gusta", "mucho"],  "validas": ["la", "el", "jugar", "comer"]},
    {"contexto": ["no", "me", "gusta"],     "validas": ["el", "la", "porque", "cuando"]},
    {"contexto": ["me", "gustó"],           "validas": ["mucho", "la", "el", "porque"]},
    {"contexto": ["no", "me", "gustó"],     "validas": ["porque", "la", "el", "cuando"]},
    {"contexto": ["qué", "rico"],           "validas": ["está", "es", "el", "la"]},
    {"contexto": ["qué", "bueno"],          "validas": ["está", "es", "que", "porque"]},
    {"contexto": ["qué", "lindo"],          "validas": ["está", "es", "el", "la"]},
    {"contexto": ["qué", "feo"],            "validas": ["está", "es", "el", "la"]},
    {"contexto": ["qué", "frío"],           "validas": ["está", "hace", "el", "la"]},
    {"contexto": ["qué", "calor"],          "validas": ["hace", "hay", "afuera", "hoy"]},
    {"contexto": ["tengo", "miedo"],        "validas": ["de", "porque", "al", "hoy"]},
    {"contexto": ["tengo", "miedo", "de"],  "validas": ["ir", "el", "la", "los", "que"]},
    {"contexto": ["estoy", "listo"],        "validas": ["para", "porque", "y", "hoy"]},
    {"contexto": ["estoy", "lista"],        "validas": ["para", "porque", "y", "hoy"]},
    {"contexto": ["ya", "estoy"],           "validas": ["listo", "lista", "porque", "bien"]},
    {"contexto": ["todavía", "no"],         "validas": ["quiero", "puedo", "tengo", "estoy"]},
    {"contexto": ["ya", "no"],              "validas": ["quiero", "puedo", "tengo", "estoy"]},
    {"contexto": ["solo", "quiero"],        "validas": ["ir", "comer", "dormir", "descansar"]},
    {"contexto": ["sola", "quiero"],        "validas": ["ir", "comer", "dormir", "descansar"]},
    {"contexto": ["con", "quién"],          "validas": ["voy", "quiero", "puedo", "tengo"]},
    {"contexto": ["dónde", "está"],         "validas": ["mi", "el", "la", "porque"]},
    {"contexto": ["cuándo", "vamos"],       "validas": ["al", "a", "con", "porque"]},
    {"contexto": ["cómo", "estás"],         "validas": ["hoy", "porque", "y", "bien"]},
    {"contexto": ["por", "favor"],          "validas": ["quiero", "necesito", "puedo", "dame"]},
    {"contexto": ["muchas", "gracias"],     "validas": ["por", "porque", "y", "hoy"]},
]

# ── Modelo en numpy ────────────────────────────────────────────────────────────

def _sigmoide(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def _softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


class PredictorLSTM:
    def __init__(self, ruta_npz, ruta_json):
        with open(ruta_json, encoding="utf-8") as f:
            cfg = json.load(f)
        pesos = np.load(ruta_npz)

        self.vocab    = cfg["vocab"]
        self.idx      = {w: i for i, w in enumerate(self.vocab)}
        self.contexto = cfg["contexto"]
        self.emb      = pesos["embedding.weight"]
        self.lstm_ih  = pesos["lstm.weight_ih_l0"]
        self.lstm_hh  = pesos["lstm.weight_hh_l0"]
        self.lstm_bih = pesos["lstm.bias_ih_l0"]
        self.lstm_bhh = pesos["lstm.bias_hh_l0"]
        self.w_sal    = pesos["salida.weight"]
        self.b_sal    = pesos["salida.bias"]
        self.H        = self.lstm_hh.shape[1]

    def _lstm_step(self, x, h, c):
        H = self.H
        gates = self.lstm_ih @ x + self.lstm_hh @ h + self.lstm_bih + self.lstm_bhh
        i_g = _sigmoide(gates[:H])
        f   = _sigmoide(gates[H:2*H])
        g   = np.tanh(gates[2*H:3*H])
        o   = _sigmoide(gates[3*H:])
        c_new = f * c + i_g * g
        h_new = o * np.tanh(c_new)
        return h_new, c_new

    def predecir_top3(self, palabras):
        unk    = self.idx.get("<unk>", 1)
        inicio = self.idx.get("<s>", 2)
        _PALABRA = re.compile(r"[a-záéíóúüñ]+")
        tokens = []
        for p in palabras:
            tokens.extend(_PALABRA.findall(p.lower()))

        seq = [inicio] * self.contexto
        for t in tokens:
            seq.append(self.idx.get(t, unk))
        seq = seq[-self.contexto:]

        h = np.zeros(self.H, dtype=np.float32)
        c = np.zeros(self.H, dtype=np.float32)
        for idx_w in seq:
            x = self.emb[idx_w]
            h, c = self._lstm_step(x, h, c)

        logits = self.w_sal @ h + self.b_sal
        probs  = _softmax(logits)
        top3_idx = np.argpartition(-probs, 3)[:3]
        top3_idx = top3_idx[np.argsort(-probs[top3_idx])]
        return [(self.vocab[i], round(float(probs[i]) * 100, 2)) for i in top3_idx]


# ── Evaluación ─────────────────────────────────────────────────────────────────

def evaluar():
    print("Cargando modelo...")
    modelo = PredictorLSTM(RUTA_NPZ, RUTA_JSON)
    print(f"Vocabulario: {len(modelo.vocab):,} palabras")
    print(f"Dataset de prueba: {len(DATASET_PRUEBA)} casos\n")

    print("=" * 70)
    print(f"{'CONTEXTO':<32} {'TOP 3':<30} {'OK'}")
    print("=" * 70)

    total    = 0
    aciertos = 0

    for caso in DATASET_PRUEBA:
        ctx    = caso["contexto"]
        validas = set(caso["validas"])
        top3   = modelo.predecir_top3(ctx)
        top3_palabras = [w for w, _ in top3]
        top3_str = ", ".join(f"{w}({p:.0f}%)" for w, p in top3)

        ok = any(w in validas for w in top3_palabras)
        if ok:
            aciertos += 1
        total += 1

        ctx_str = " ".join(ctx)
        marca   = "✓" if ok else "✗"
        print(f"{ctx_str:<32} {top3_str:<38} {marca}")

    print("=" * 70)
    pct = aciertos / total * 100
    print(f"\nResultados: {aciertos}/{total} casos con al menos una palabra válida en top 3")
    print(f"Accuracy top-3 (palabras válidas): {pct:.1f}%\n")

    print("── Desglose por longitud de contexto ──")
    for largo in [1, 2, 3, 4]:
        casos = [c for c in DATASET_PRUEBA if len(c["contexto"]) == largo]
        if not casos:
            continue
        ac = sum(
            1 for caso in casos
            if any(w in set(caso["validas"]) for w, _ in modelo.predecir_top3(caso["contexto"]))
        )
        print(f"  Contexto de {largo} palabra(s): {ac}/{len(casos)} = {ac/len(casos)*100:.1f}%")


if __name__ == "__main__":
    evaluar()
