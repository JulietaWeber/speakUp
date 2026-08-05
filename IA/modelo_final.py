import spacy
import numpy as np
import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# ── Cargar modelo spaCy en español ───────────────────────────────────────────

print("Cargando spaCy...")
nlp = spacy.load("es_core_news_md")
print("spaCy cargado\n")

# ── Dataset ───────────────────────────────────────────────────────────────────

historial = [

    # ================= CASA =================
    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:05", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:10", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:15", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:20", "frase": ["quiero", "comer"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:25", "frase": ["quiero", "comer"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:30", "frase": ["quiero", "comer"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:35", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:40", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:45", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:00", "frase": ["quiero", "descansar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:10", "frase": ["quiero", "descansar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:20", "frase": ["quiero", "jugar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:30", "frase": ["quiero", "jugar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:40", "frase": ["necesito", "ayuda"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:50", "frase": ["necesito", "ayuda"]},
    {"categoria": "Casa", "fecha": "2026-06-01 10:00", "frase": ["tengo", "hambre"]},
    {"categoria": "Casa", "fecha": "2026-06-01 10:10", "frase": ["tengo", "hambre"]},
    {"categoria": "Casa", "fecha": "2026-06-01 10:20", "frase": ["tengo", "hambre"]},
    {"categoria": "Casa", "fecha": "2026-06-01 10:30", "frase": ["tengo", "sed"]},
    {"categoria": "Casa", "fecha": "2026-06-01 10:40", "frase": ["tengo", "sed"]},
    {"categoria": "Casa", "fecha": "2026-06-01 10:50", "frase": ["tengo", "sueño"]},
    {"categoria": "Casa", "fecha": "2026-06-01 11:00", "frase": ["tengo", "sueño"]},
    {"categoria": "Casa", "fecha": "2026-06-01 11:10", "frase": ["tengo", "sueño"]},
    {"categoria": "Casa", "fecha": "2026-06-01 11:20", "frase": ["quiero", "dormir"]},
    {"categoria": "Casa", "fecha": "2026-06-01 11:30", "frase": ["quiero", "dormir"]},
    {"categoria": "Casa", "fecha": "2026-06-01 11:40", "frase": ["quiero", "música"]},
    {"categoria": "Casa", "fecha": "2026-06-01 11:50", "frase": ["quiero", "música"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:00", "frase": ["quiero", "salir", "afuera"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:10", "frase": ["quiero", "salir", "afuera"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:20", "frase": ["quiero", "hablar", "mamá"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:30", "frase": ["quiero", "hablar", "mamá"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:40", "frase": ["quiero", "hablar", "papá"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:50", "frase": ["quiero", "hablar", "papá"]},
    {"categoria": "Casa", "fecha": "2026-06-01 13:00", "frase": ["quiero", "ver", "película"]},
    {"categoria": "Casa", "fecha": "2026-06-01 13:10", "frase": ["quiero", "ver", "película"]},
    {"categoria": "Casa", "fecha": "2026-06-01 13:20", "frase": ["quiero", "jugar", "videojuegos"]},
    {"categoria": "Casa", "fecha": "2026-06-01 13:30", "frase": ["quiero", "jugar", "videojuegos"]},
    {"categoria": "Casa", "fecha": "2026-06-01 13:40", "frase": ["quiero", "dibujar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 13:50", "frase": ["quiero", "dibujar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 14:00", "frase": ["necesito", "abrigo"]},
    {"categoria": "Casa", "fecha": "2026-06-01 14:10", "frase": ["necesito", "abrigo"]},
    {"categoria": "Casa", "fecha": "2026-06-01 14:20", "frase": ["tengo", "frío"]},
    {"categoria": "Casa", "fecha": "2026-06-01 14:30", "frase": ["tengo", "frío"]},
    {"categoria": "Casa", "fecha": "2026-06-01 14:40", "frase": ["tengo", "calor"]},
    {"categoria": "Casa", "fecha": "2026-06-01 14:50", "frase": ["tengo", "calor"]},
    {"categoria": "Casa", "fecha": "2026-06-01 15:00", "frase": ["quiero", "bañarme"]},
    {"categoria": "Casa", "fecha": "2026-06-01 15:10", "frase": ["quiero", "bañarme"]},
    {"categoria": "Casa", "fecha": "2026-06-01 15:20", "frase": ["necesito", "toalla"]},
    {"categoria": "Casa", "fecha": "2026-06-01 15:30", "frase": ["necesito", "ropa"]},
    {"categoria": "Casa", "fecha": "2026-06-01 15:40", "frase": ["quiero", "llamar", "abuela"]},
    {"categoria": "Casa", "fecha": "2026-06-01 15:50", "frase": ["quiero", "llamar", "abuela"]},
    {"categoria": "Casa", "fecha": "2026-06-01 16:00", "frase": ["quiero", "leer", "libro"]},
    {"categoria": "Casa", "fecha": "2026-06-01 16:10", "frase": ["quiero", "leer", "libro"]},
    {"categoria": "Casa", "fecha": "2026-06-01 16:20", "frase": ["quiero", "abrazar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 16:30", "frase": ["quiero", "abrazar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 16:40", "frase": ["necesito", "silencio"]},
    {"categoria": "Casa", "fecha": "2026-06-01 16:50", "frase": ["necesito", "silencio"]},
    {"categoria": "Casa", "fecha": "2026-06-01 17:00", "frase": ["quiero", "comer", "algo"]},
    {"categoria": "Casa", "fecha": "2026-06-01 17:10", "frase": ["quiero", "comer", "algo"]},
    {"categoria": "Casa", "fecha": "2026-06-01 17:20", "frase": ["quiero", "tomar", "jugo"]},
    {"categoria": "Casa", "fecha": "2026-06-01 17:30", "frase": ["quiero", "tomar", "jugo"]},
    {"categoria": "Casa", "fecha": "2026-06-01 17:40", "frase": ["necesito", "ir", "baño"]},
    {"categoria": "Casa", "fecha": "2026-06-01 17:50", "frase": ["necesito", "ir", "baño"]},
    {"categoria": "Casa", "fecha": "2026-06-01 18:00", "frase": ["necesito", "ir", "baño"]},
    {"categoria": "Casa", "fecha": "2026-06-01 18:10", "frase": ["quiero", "pasear", "perro"]},
    {"categoria": "Casa", "fecha": "2026-06-01 18:20", "frase": ["quiero", "pasear", "perro"]},
    {"categoria": "Casa", "fecha": "2026-06-01 18:30", "frase": ["apagar", "luz"]},
    {"categoria": "Casa", "fecha": "2026-06-01 18:40", "frase": ["prender", "luz"]},
    {"categoria": "Casa", "fecha": "2026-06-01 18:50", "frase": ["cerrar", "puerta"]},
    {"categoria": "Casa", "fecha": "2026-06-01 19:00", "frase": ["abrir", "ventana"]},
    {"categoria": "Casa", "fecha": "2026-06-01 19:10", "frase": ["necesito", "cargador", "celular"]},
    {"categoria": "Casa", "fecha": "2026-06-01 19:20", "frase": ["necesito", "cargador", "celular"]},

    # ================= ESCUELA =================
    {"categoria": "Escuela", "fecha": "2026-06-02 08:00", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:05", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:10", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:15", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:20", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:25", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:30", "frase": ["necesito", "ayuda"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:35", "frase": ["necesito", "ayuda"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:40", "frase": ["necesito", "ayuda"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:45", "frase": ["quiero", "participar"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:50", "frase": ["quiero", "participar"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:55", "frase": ["no", "entiendo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:00", "frase": ["no", "entiendo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:05", "frase": ["quiero", "hacer", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:10", "frase": ["quiero", "hacer", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:15", "frase": ["terminé", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:20", "frase": ["terminé", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:25", "frase": ["me", "gusta", "escuela"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:30", "frase": ["no", "quiero", "ir", "escuela"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:35", "frase": ["no", "quiero", "ir", "escuela"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:40", "frase": ["quiero", "ir", "recreo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:45", "frase": ["quiero", "ir", "recreo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:50", "frase": ["necesito", "lápiz"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:55", "frase": ["necesito", "lápiz"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:00", "frase": ["necesito", "borrador"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:05", "frase": ["necesito", "borrador"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:10", "frase": ["necesito", "tijeras"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:15", "frase": ["perdí", "cuaderno"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:20", "frase": ["perdí", "cuaderno"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:25", "frase": ["no", "escucho", "maestra"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:30", "frase": ["no", "escucho", "maestra"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:35", "frase": ["quiero", "hablar", "maestra"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:40", "frase": ["quiero", "hablar", "maestra"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:45", "frase": ["tengo", "miedo", "prueba"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:50", "frase": ["tengo", "miedo", "prueba"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 10:55", "frase": ["quiero", "trabajar", "grupo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:00", "frase": ["quiero", "trabajar", "grupo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:05", "frase": ["me", "molesta", "ruido"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:10", "frase": ["me", "molesta", "ruido"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:15", "frase": ["quiero", "ir", "baño"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:20", "frase": ["quiero", "ir", "baño"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:25", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:30", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:35", "frase": ["aprendí", "algo", "nuevo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:40", "frase": ["no", "entiendo", "consigna"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:45", "frase": ["no", "entiendo", "consigna"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:50", "frase": ["quiero", "mostrar", "trabajo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 11:55", "frase": ["quiero", "mostrar", "trabajo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:00", "frase": ["me", "cansé", "escuela"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:05", "frase": ["quiero", "ir", "biblioteca"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:10", "frase": ["quiero", "usar", "computadora"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:15", "frase": ["quiero", "usar", "computadora"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:20", "frase": ["compañero", "me", "molesta"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:25", "frase": ["compañero", "me", "molesta"]},

    # ================= MÉDICO =================
    {"categoria": "Médico", "fecha": "2026-06-03 09:00", "frase": ["me", "duele", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:05", "frase": ["me", "duele", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:10", "frase": ["me", "duele", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:15", "frase": ["me", "duele", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:20", "frase": ["me", "duele", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:25", "frase": ["me", "duele", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:30", "frase": ["me", "duele", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:35", "frase": ["me", "duele", "garganta"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:40", "frase": ["me", "duele", "garganta"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:45", "frase": ["me", "duele", "oído"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:50", "frase": ["me", "duele", "oído"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:55", "frase": ["me", "duele", "brazo"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:00", "frase": ["me", "duele", "pierna"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:05", "frase": ["me", "duele", "espalda"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:10", "frase": ["tengo", "fiebre"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:15", "frase": ["tengo", "fiebre"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:20", "frase": ["tengo", "fiebre"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:25", "frase": ["necesito", "medicamento"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:30", "frase": ["necesito", "medicamento"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:35", "frase": ["me", "siento", "mejor"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:40", "frase": ["me", "siento", "mejor"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:45", "frase": ["me", "siento", "mal"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:50", "frase": ["me", "siento", "mal"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:55", "frase": ["quiero", "descansar"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:00", "frase": ["necesito", "ayuda"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:05", "frase": ["quiero", "volver", "casa"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:10", "frase": ["quiero", "volver", "casa"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:15", "frase": ["tengo", "náuseas"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:20", "frase": ["tengo", "náuseas"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:25", "frase": ["tengo", "mareos"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:30", "frase": ["tengo", "mareos"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:35", "frase": ["me", "lastimé"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:40", "frase": ["me", "lastimé"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:45", "frase": ["necesito", "curita"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:50", "frase": ["necesito", "curita"]},
    {"categoria": "Médico", "fecha": "2026-06-03 11:55", "frase": ["necesito", "ir", "médico"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:00", "frase": ["necesito", "ir", "médico"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:05", "frase": ["tengo", "alergia"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:10", "frase": ["tengo", "alergia"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:15", "frase": ["no", "puedo", "respirar"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:20", "frase": ["necesito", "inhalador"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:25", "frase": ["necesito", "inhalador"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:30", "frase": ["me", "sangra", "dedo"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:35", "frase": ["tengo", "fiebre", "alta"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:40", "frase": ["quiero", "mamá", "médico"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:45", "frase": ["quiero", "mamá", "médico"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:50", "frase": ["me", "duele", "muela"]},
    {"categoria": "Médico", "fecha": "2026-06-03 12:55", "frase": ["me", "duele", "muela"]},

    # ================= EMOCIONES =================
    {"categoria": "Emociones", "fecha": "2026-06-04 08:00", "frase": ["estoy", "feliz"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:05", "frase": ["estoy", "feliz"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:10", "frase": ["estoy", "feliz"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:15", "frase": ["estoy", "triste"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:20", "frase": ["estoy", "triste"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:25", "frase": ["estoy", "triste"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:30", "frase": ["estoy", "enojado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:35", "frase": ["estoy", "enojado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:40", "frase": ["estoy", "enojado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:45", "frase": ["tengo", "miedo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:50", "frase": ["tengo", "miedo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 08:55", "frase": ["tengo", "miedo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:00", "frase": ["estoy", "nervioso"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:05", "frase": ["estoy", "nervioso"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:10", "frase": ["estoy", "tranquilo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:15", "frase": ["estoy", "tranquilo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:20", "frase": ["estoy", "cansado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:25", "frase": ["estoy", "cansado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:30", "frase": ["estoy", "aburrido"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:35", "frase": ["estoy", "aburrido"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:40", "frase": ["estoy", "contento"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:45", "frase": ["estoy", "contento"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:50", "frase": ["me", "siento", "solo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 09:55", "frase": ["me", "siento", "solo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:00", "frase": ["me", "siento", "bien"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:05", "frase": ["me", "siento", "bien"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:10", "frase": ["me", "siento", "mal"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:15", "frase": ["me", "siento", "mal"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:20", "frase": ["quiero", "llorar"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:25", "frase": ["quiero", "llorar"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:30", "frase": ["necesito", "abrazo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:35", "frase": ["necesito", "abrazo"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:40", "frase": ["necesito", "calmarme"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:45", "frase": ["necesito", "calmarme"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:50", "frase": ["estoy", "preocupado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 10:55", "frase": ["estoy", "preocupado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:00", "frase": ["estoy", "emocionado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:05", "frase": ["estoy", "emocionado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:10", "frase": ["me", "da", "vergüenza"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:15", "frase": ["me", "da", "vergüenza"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:20", "frase": ["extraño", "familia"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:25", "frase": ["extraño", "familia"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:30", "frase": ["necesito", "ayuda"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:35", "frase": ["quiero", "hablar"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:40", "frase": ["quiero", "hablar"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:45", "frase": ["no", "quiero", "hablar"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:50", "frase": ["no", "quiero", "hablar"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 11:55", "frase": ["estoy", "frustrado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 12:00", "frase": ["estoy", "frustrado"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 12:05", "frase": ["me", "siento", "confundido"]},
    {"categoria": "Emociones", "fecha": "2026-06-04 12:10", "frase": ["me", "siento", "orgulloso"]},

    # ================= TRANSPORTE =================
    {"categoria": "Transporte", "fecha": "2026-06-05 07:00", "frase": ["quiero", "ir", "escuela"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:05", "frase": ["quiero", "ir", "escuela"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:10", "frase": ["quiero", "ir", "escuela"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:15", "frase": ["espero", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:20", "frase": ["espero", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:25", "frase": ["quiero", "volver", "casa"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:30", "frase": ["quiero", "volver", "casa"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:35", "frase": ["quiero", "volver", "casa"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:40", "frase": ["necesito", "bajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:45", "frase": ["necesito", "bajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:50", "frase": ["quiero", "viajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 07:55", "frase": ["quiero", "viajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:00", "frase": ["llegamos", "destino"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:05", "frase": ["llegamos", "destino"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:10", "frase": ["perdí", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:15", "frase": ["perdí", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:20", "frase": ["estoy", "perdido"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:25", "frase": ["estoy", "perdido"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:30", "frase": ["necesito", "ayuda", "llegar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:35", "frase": ["necesito", "ayuda", "llegar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:40", "frase": ["quiero", "ir", "taxi"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:45", "frase": ["quiero", "ir", "taxi"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:50", "frase": ["quiero", "ir", "subte"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 08:55", "frase": ["quiero", "ir", "subte"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:00", "frase": ["cuánto", "falta", "llegar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:05", "frase": ["cuánto", "falta", "llegar"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:10", "frase": ["tengo", "mareos", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:15", "frase": ["necesito", "cargar", "sube"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:20", "frase": ["necesito", "cargar", "sube"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:25", "frase": ["quiero", "sentar", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:30", "frase": ["quiero", "sentar", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:35", "frase": ["llegué", "aviso"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:40", "frase": ["llegué", "aviso"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:45", "frase": ["hay", "tráfico"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:50", "frase": ["hay", "tráfico"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 09:55", "frase": ["quiero", "ir", "bicicleta"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:00", "frase": ["quiero", "ir", "bicicleta"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:05", "frase": ["quiero", "ir", "caminando"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:10", "frase": ["quiero", "ir", "caminando"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:15", "frase": ["está", "lloviendo"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:20", "frase": ["necesito", "paraguas"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:25", "frase": ["el", "auto", "roto"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:30", "frase": ["necesito", "remis"]},
    {"categoria": "Transporte", "fecha": "2026-06-05 10:35", "frase": ["necesito", "remis"]},

    # ================= AMIGOS =================
    {"categoria": "Amigos", "fecha": "2026-06-06 15:00", "frase": ["quiero", "jugar", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:05", "frase": ["quiero", "jugar", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:10", "frase": ["quiero", "jugar", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:15", "frase": ["quiero", "hablar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:20", "frase": ["quiero", "hablar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:25", "frase": ["quiero", "salir", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:30", "frase": ["quiero", "salir", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:35", "frase": ["estoy", "feliz", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:40", "frase": ["estoy", "feliz", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:45", "frase": ["quiero", "compartir"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:50", "frase": ["quiero", "compartir"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 15:55", "frase": ["extraño", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:00", "frase": ["extraño", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:05", "frase": ["extraño", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:10", "frase": ["peleé", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:15", "frase": ["peleé", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:20", "frase": ["quiero", "pedir", "perdón"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:25", "frase": ["quiero", "pedir", "perdón"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:30", "frase": ["quiero", "llamar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:35", "frase": ["quiero", "llamar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:40", "frase": ["amigo", "cumpleaños"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:45", "frase": ["amigo", "cumpleaños"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:50", "frase": ["quiero", "invitar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 16:55", "frase": ["quiero", "invitar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:00", "frase": ["amigo", "me", "ayudó"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:05", "frase": ["quiero", "ayudar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:10", "frase": ["quiero", "ayudar", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:15", "frase": ["amigo", "está", "triste"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:20", "frase": ["amigo", "está", "triste"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:25", "frase": ["quiero", "nuevo", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:30", "frase": ["quiero", "nuevo", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:35", "frase": ["me", "ignoran", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:40", "frase": ["quiero", "jugar", "parque"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:45", "frase": ["quiero", "jugar", "parque"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:50", "frase": ["quiero", "foto", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 17:55", "frase": ["quiero", "foto", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:00", "frase": ["amigo", "se", "mudó"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:05", "frase": ["amigo", "se", "mudó"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:10", "frase": ["quiero", "chatear", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:15", "frase": ["quiero", "chatear", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:20", "frase": ["amigo", "no", "contesta"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:25", "frase": ["quiero", "regalo", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:30", "frase": ["quiero", "regalo", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:35", "frase": ["amigo", "me", "prestó"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:40", "frase": ["quiero", "ver", "amigo"]},
    {"categoria": "Amigos", "fecha": "2026-06-06 18:45", "frase": ["quiero", "ver", "amigo"]},
]

# ── Funciones de vectorización ────────────────────────────────────────────────

def palabra_a_vector(palabra):
    """Convierte una palabra a su vector spaCy de 96 dimensiones."""
    return nlp(palabra.lower()).vector

def categoria_a_vector(categoria):
    """Convierte una categoría a su vector spaCy, igual que las palabras.
    Así el modelo acepta cualquier categoría nueva sin necesitar reentrenar."""
    return nlp(categoria.lower()).vector

# ── Generación de datos de entrenamiento ──────────────────────────────────────

datos_entrenamiento = []
for registro in historial:
    categoria = registro["categoria"]
    frase = registro["frase"]
    for i in range(len(frase) - 1):
        datos_entrenamiento.append((categoria, frase[i], frase[i + 1]))

print(f"Pares generados: {len(datos_entrenamiento)}")

# ── Encoders ──────────────────────────────────────────────────────────────────

encoder_salida = LabelEncoder()
encoder_salida.fit([d[2] for d in datos_entrenamiento])

# ── Construcción de X e y ─────────────────────────────────────────────────────

X, y = [], []
for categoria, palabra_actual, palabra_siguiente in datos_entrenamiento:
    X.append(np.concatenate([
        categoria_a_vector(categoria),
        palabra_a_vector(palabra_actual)
    ]))
    y.append(encoder_salida.transform([palabra_siguiente])[0])

X = np.array(X)
y = np.array(y)

# ── División training / testing ───────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training: {len(X_train)} | Testing: {len(X_test)}\n")

# ── Red Neuronal ──────────────────────────────────────────────────────────────

modelo = MLPClassifier(
    hidden_layer_sizes=(128, 64),
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
print("Modelo guardado: modelo_base.pkl\n")

# ── Prueba ────────────────────────────────────────────────────────────────────

print("── Prueba de predicciones ──")
ejemplos = [
    ("Casa",       "quiero"),
    ("Escuela",    "necesito"),
    ("Médico",     "me"),
    ("Emociones",  "estoy"),
    ("Transporte", "quiero"),
    ("Amigos",     "extraño"),
]

for categoria, palabra in ejemplos:
    entrada = np.concatenate([
        categoria_a_vector(categoria),
        palabra_a_vector(palabra)
    ]).reshape(1, -1)
    probs = modelo.predict_proba(entrada)[0]
    top3 = probs.argsort()[-3:][::-1]
    print(f"\n'{palabra}' en {categoria}:")
    for i in top3:
        p = encoder_salida.inverse_transform([modelo.classes_[i]])[0]
        print(f"  - {p} ({round(probs[i]*100, 2)}%)")