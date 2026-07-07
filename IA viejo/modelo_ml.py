from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

historial = [

    # ================= CASA =================

    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:05", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:10", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:15", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:20", "frase": ["quiero", "ver", "televisión"]},

    {"categoria": "Casa", "fecha": "2026-06-01 08:30", "frase": ["quiero", "comer"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:35", "frase": ["quiero", "comer"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:40", "frase": ["quiero", "comer"]},

    {"categoria": "Casa", "fecha": "2026-06-01 08:50", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:55", "frase": ["quiero", "tomar", "agua"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:00", "frase": ["quiero", "tomar", "agua"]},

    {"categoria": "Casa", "fecha": "2026-06-01 09:10", "frase": ["quiero", "descansar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:20", "frase": ["quiero", "descansar"]},

    {"categoria": "Casa", "fecha": "2026-06-01 09:30", "frase": ["quiero", "jugar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 09:40", "frase": ["quiero", "jugar"]},

    {"categoria": "Casa", "fecha": "2026-06-01 09:50", "frase": ["necesito", "ayuda"]},

    # ================= ESCUELA =================

    {"categoria": "Escuela", "fecha": "2026-06-02 08:00", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:05", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:10", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:15", "frase": ["quiero", "leer"]},

    {"categoria": "Escuela", "fecha": "2026-06-02 08:25", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:30", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:35", "frase": ["quiero", "escribir"]},

    {"categoria": "Escuela", "fecha": "2026-06-02 08:45", "frase": ["necesito", "ayuda"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 08:50", "frase": ["necesito", "ayuda"]},

    {"categoria": "Escuela", "fecha": "2026-06-02 09:00", "frase": ["quiero", "participar"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:10", "frase": ["quiero", "participar"]},

    {"categoria": "Escuela", "fecha": "2026-06-02 09:20", "frase": ["no", "entiendo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:30", "frase": ["quiero", "hacer", "la", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:40", "frase": ["terminé", "la", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:50", "frase": ["me", "gusta", "la", "escuela"]},

    # ================= MÉDICO =================

    {"categoria": "Médico", "fecha": "2026-06-03 09:00", "frase": ["me", "duele", "la", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:05", "frase": ["me", "duele", "la", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:10", "frase": ["me", "duele", "la", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:15", "frase": ["me", "duele", "la", "cabeza"]},

    {"categoria": "Médico", "fecha": "2026-06-03 09:25", "frase": ["me", "duele", "el", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:30", "frase": ["me", "duele", "el", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:35", "frase": ["me", "duele", "el", "estómago"]},

    {"categoria": "Médico", "fecha": "2026-06-03 09:45", "frase": ["tengo", "fiebre"]},
    {"categoria": "Médico", "fecha": "2026-06-03 09:50", "frase": ["tengo", "fiebre"]},

    {"categoria": "Médico", "fecha": "2026-06-03 10:00", "frase": ["necesito", "medicamento"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:05", "frase": ["necesito", "medicamento"]},

    {"categoria": "Médico", "fecha": "2026-06-03 10:15", "frase": ["me", "siento", "mejor"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:25", "frase": ["me", "siento", "mal"]},

    {"categoria": "Médico", "fecha": "2026-06-03 10:35", "frase": ["quiero", "descansar"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:45", "frase": ["necesito", "ayuda"]},
    {"categoria": "Médico", "fecha": "2026-06-03 10:55", "frase": ["quiero", "volver", "a", "casa"]},

    # CASA
    {"categoria": "Casa", "fecha": "2026-06-09 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-09 10:00", "frase": ["quiero", "comer"]},
    {"categoria": "Casa", "fecha": "2026-06-09 14:00", "frase": ["quiero", "descansar"]},
    {"categoria": "Casa", "fecha": "2026-06-09 18:00", "frase": ["tengo", "hambre"]},
    {"categoria": "Casa", "fecha": "2026-06-10 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-10 13:00", "frase": ["quiero", "ayudar", "mamá"]},
    {"categoria": "Casa", "fecha": "2026-06-10 20:00", "frase": ["tengo", "sueño"]},
    {"categoria": "Casa", "fecha": "2026-06-10 21:00", "frase": ["quiero", "ver", "televisión"]},

    # ESCUELA
    {"categoria": "Escuela", "fecha": "2026-06-09 08:00", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-09 09:00", "frase": ["necesito", "ayuda"]},
    {"categoria": "Escuela", "fecha": "2026-06-09 10:00", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-09 11:00", "frase": ["no", "entiendo"]},
    {"categoria": "Escuela", "fecha": "2026-06-10 08:00", "frase": ["quiero", "leer"]},
    {"categoria": "Escuela", "fecha": "2026-06-10 09:00", "frase": ["quiero", "participar"]},
    {"categoria": "Escuela", "fecha": "2026-06-10 11:00", "frase": ["terminé", "la", "tarea"]},
    {"categoria": "Escuela", "fecha": "2026-06-10 12:00", "frase": ["necesito", "ayuda"]},

    # MEDICO
    {"categoria": "Médico", "fecha": "2026-06-09 08:00", "frase": ["me", "duele", "la", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-09 09:00", "frase": ["me", "duele", "el", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-09 10:00", "frase": ["necesito", "medicamento"]},
    {"categoria": "Médico", "fecha": "2026-06-09 12:00", "frase": ["tengo", "fiebre"]},
    {"categoria": "Médico", "fecha": "2026-06-10 08:00", "frase": ["me", "siento", "mejor"]},
    {"categoria": "Médico", "fecha": "2026-06-10 09:00", "frase": ["quiero", "descansar"]},
    {"categoria": "Médico", "fecha": "2026-06-10 10:00", "frase": ["me", "duele", "la", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-10 12:00", "frase": ["necesito", "medicamento"]},

    # AMIGOS
    {"categoria": "Amigos", "fecha": "2026-06-09 15:00", "frase": ["quiero", "jugar"]},
    {"categoria": "Amigos", "fecha": "2026-06-09 16:00", "frase": ["quiero", "hablar"]},
    {"categoria": "Amigos", "fecha": "2026-06-09 17:00", "frase": ["quiero", "salir"]},
    {"categoria": "Amigos", "fecha": "2026-06-09 18:00", "frase": ["estoy", "feliz"]},
    {"categoria": "Amigos", "fecha": "2026-06-10 15:00", "frase": ["quiero", "jugar"]},
    {"categoria": "Amigos", "fecha": "2026-06-10 16:00", "frase": ["quiero", "compartir"]},
    {"categoria": "Amigos", "fecha": "2026-06-10 17:00", "frase": ["extraño", "a", "mis", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-10 18:00", "frase": ["quiero", "hablar"]},

    # TRANSPORTE
    {"categoria": "Transporte", "fecha": "2026-06-09 07:00", "frase": ["quiero", "ir", "a", "la", "escuela"]},
    {"categoria": "Transporte", "fecha": "2026-06-09 08:00", "frase": ["espero", "el", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-09 17:00", "frase": ["quiero", "volver", "a", "casa"]},
    {"categoria": "Transporte", "fecha": "2026-06-09 18:00", "frase": ["necesito", "bajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-10 07:00", "frase": ["quiero", "viajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-10 08:00", "frase": ["llegamos", "al", "destino"]},
    {"categoria": "Transporte", "fecha": "2026-06-10 17:00", "frase": ["quiero", "volver", "a", "casa"]},
    {"categoria": "Transporte", "fecha": "2026-06-10 18:00", "frase": ["espero", "el", "colectivo"]},

    # EMOCIONES
    {"categoria": "Emociones", "fecha": "2026-06-09 20:00", "frase": ["estoy", "feliz"]},
    {"categoria": "Emociones", "fecha": "2026-06-09 20:30", "frase": ["estoy", "triste"]},
    {"categoria": "Emociones", "fecha": "2026-06-09 21:00", "frase": ["tengo", "miedo"]},
    {"categoria": "Emociones", "fecha": "2026-06-09 21:30", "frase": ["estoy", "tranquilo"]},
    {"categoria": "Emociones", "fecha": "2026-06-10 20:00", "frase": ["estoy", "feliz"]},
    {"categoria": "Emociones", "fecha": "2026-06-10 20:30", "frase": ["estoy", "enojado"]},
    {"categoria": "Emociones", "fecha": "2026-06-10 21:00", "frase": ["necesito", "ayuda"]},
    {"categoria": "Emociones", "fecha": "2026-06-10 21:30", "frase": ["estoy", "feliz"]},
]

datos_entrenamiento = []

for registro in historial:

    categoria = registro["categoria"]
    frase = registro["frase"]

    for i in range(len(frase) - 1):

        palabra_actual = frase[i]
        palabra_siguiente = frase[i + 1]

        datos_entrenamiento.append(
            (categoria, palabra_actual, palabra_siguiente)
        )

#print("Datos de entrenamiento:")
#print(datos_entrenamiento)

encoder_categoria = LabelEncoder()
encoder_palabra = LabelEncoder()

categorias = [dato[0] for dato in datos_entrenamiento]
palabras_actuales = [dato[1] for dato in datos_entrenamiento]
palabras_siguientes = [dato[2] for dato in datos_entrenamiento]

encoder_categoria.fit(categorias)
encoder_palabra.fit(
    palabras_actuales + palabras_siguientes
)

X = []
y = []

for categoria, palabra_actual, palabra_siguiente in datos_entrenamiento:

    X.append([
        encoder_categoria.transform([categoria])[0],
        encoder_palabra.transform([palabra_actual])[0]
    ])

    y.append(
        encoder_palabra.transform([palabra_siguiente])[0]
    )

modelo = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

modelo.fit(X, y)

#joblib.dump(modelo, "modelo_base.pkl")
#joblib.dump(encoder_categoria, "encoder_categoria.pkl")
#joblib.dump(encoder_palabra, "encoder_palabra.pkl")

print("Modelo guardado correctamente")

# Entrada de prueba
entrada = [[
    encoder_categoria.transform(["Casa"])[0],
    encoder_palabra.transform(["quiero"])[0]
]]

# Obtener probabilidades
probabilidades = modelo.predict_proba(entrada)[0]

# Top 3 posiciones con mayor probabilidad
top3_indices = probabilidades.argsort()[-3:][::-1]

print()
print("Top 3 recomendaciones:")

for i, indice in enumerate(top3_indices):

    # Obtener la clase REAL asociada a esa posición
    clase_real = modelo.classes_[indice]

    # Convertir la clase a palabra
    palabra = encoder_palabra.inverse_transform([clase_real])[0]

    probabilidad = probabilidades[indice] * 100

    print(
        f"{i + 1}. {palabra} ({probabilidad:.2f}%)"
    )

modelo = joblib.load("modelo_base.pkl")
print(modelo)