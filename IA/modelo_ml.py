from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

historial = [

    # CASA
    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:15", "frase": ["quiero", "jugar", "videojuegos"]},
    {"categoria": "Casa", "fecha": "2026-06-01 12:00", "frase": ["tengo", "mucha", "hambre"]},
    {"categoria": "Casa", "fecha": "2026-06-01 21:00", "frase": ["tengo", "mucho", "sueño"]},
    {"categoria": "Casa", "fecha": "2026-06-02 17:00", "frase": ["quiero", "ayudar", "mamá"]},
    {"categoria": "Casa", "fecha": "2026-06-02 20:00", "frase": ["quiero", "descansar"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},
    {"categoria": "Casa", "fecha": "2026-06-01 08:00", "frase": ["quiero", "ver", "televisión"]},

    # ESCUELA
    {"categoria": "Escuela", "fecha": "2026-06-01 09:00", "frase": ["necesito", "ayuda"]},
    {"categoria": "Escuela", "fecha": "2026-06-01 09:30", "frase": ["quiero", "leer", "un", "libro"]},
    {"categoria": "Escuela", "fecha": "2026-06-01 10:00", "frase": ["quiero", "escribir"]},
    {"categoria": "Escuela", "fecha": "2026-06-01 11:00", "frase": ["no", "entiendo"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 09:00", "frase": ["quiero", "participar"]},
    {"categoria": "Escuela", "fecha": "2026-06-02 12:00", "frase": ["terminé", "la", "tarea"]},

    # DEPORTE
    {"categoria": "Deporte", "fecha": "2026-06-01 16:00", "frase": ["quiero", "jugar", "fútbol"]},
    {"categoria": "Deporte", "fecha": "2026-06-01 16:30", "frase": ["quiero", "entrenar"]},
    {"categoria": "Deporte", "fecha": "2026-06-01 17:00", "frase": ["estoy", "cansado"]},
    {"categoria": "Deporte", "fecha": "2026-06-02 16:00", "frase": ["quiero", "correr"]},
    {"categoria": "Deporte", "fecha": "2026-06-02 17:00", "frase": ["hice", "un", "gol"]},
    {"categoria": "Deporte", "fecha": "2026-06-02 18:00", "frase": ["necesito", "agua"]},

    # MÉDICO
    {"categoria": "Médico", "fecha": "2026-06-01 14:00", "frase": ["me", "duele", "la", "cabeza"]},
    {"categoria": "Médico", "fecha": "2026-06-01 14:30", "frase": ["me", "duele", "el", "estómago"]},
    {"categoria": "Médico", "fecha": "2026-06-01 15:00", "frase": ["necesito", "medicamento"]},
    {"categoria": "Médico", "fecha": "2026-06-02 14:00", "frase": ["me", "siento", "mejor"]},
    {"categoria": "Médico", "fecha": "2026-06-02 15:00", "frase": ["quiero", "descansar"]},
    {"categoria": "Médico", "fecha": "2026-06-02 16:00", "frase": ["tengo", "fiebre"]},

    # AMIGOS
    {"categoria": "Amigos", "fecha": "2026-06-01 18:00", "frase": ["quiero", "jugar"]},
    {"categoria": "Amigos", "fecha": "2026-06-01 18:30", "frase": ["quiero", "hablar"]},
    {"categoria": "Amigos", "fecha": "2026-06-01 19:00", "frase": ["extraño", "a", "mis", "amigos"]},
    {"categoria": "Amigos", "fecha": "2026-06-02 18:00", "frase": ["quiero", "salir"]},
    {"categoria": "Amigos", "fecha": "2026-06-02 18:30", "frase": ["estoy", "feliz"]},
    {"categoria": "Amigos", "fecha": "2026-06-02 19:00", "frase": ["quiero", "compartir"]},

    # COMPRAS
    {"categoria": "Compras", "fecha": "2026-06-01 11:00", "frase": ["quiero", "comprar", "pan"]},
    {"categoria": "Compras", "fecha": "2026-06-01 11:30", "frase": ["necesito", "leche"]},
    {"categoria": "Compras", "fecha": "2026-06-01 12:00", "frase": ["cuánto", "cuesta"]},
    {"categoria": "Compras", "fecha": "2026-06-02 11:00", "frase": ["quiero", "mirar", "juguetes"]},
    {"categoria": "Compras", "fecha": "2026-06-02 11:30", "frase": ["necesito", "ayuda"]},
    {"categoria": "Compras", "fecha": "2026-06-02 12:00", "frase": ["quiero", "pagar"]},

    # TRANSPORTE
    {"categoria": "Transporte", "fecha": "2026-06-01 07:00", "frase": ["quiero", "ir", "a", "la", "escuela"]},
    {"categoria": "Transporte", "fecha": "2026-06-01 17:00", "frase": ["quiero", "volver", "a", "casa"]},
    {"categoria": "Transporte", "fecha": "2026-06-01 17:30", "frase": ["espero", "el", "colectivo"]},
    {"categoria": "Transporte", "fecha": "2026-06-02 07:00", "frase": ["necesito", "bajar"]},
    {"categoria": "Transporte", "fecha": "2026-06-02 17:00", "frase": ["llegamos", "al", "destino"]},
    {"categoria": "Transporte", "fecha": "2026-06-02 18:00", "frase": ["quiero", "viajar"]},

    # EMOCIONES
    {"categoria": "Emociones", "fecha": "2026-06-01 20:00", "frase": ["estoy", "feliz"]},
    {"categoria": "Emociones", "fecha": "2026-06-01 20:30", "frase": ["estoy", "triste"]},
    {"categoria": "Emociones", "fecha": "2026-06-01 21:00", "frase": ["tengo", "miedo"]},
    {"categoria": "Emociones", "fecha": "2026-06-02 20:00", "frase": ["estoy", "enojado"]},
    {"categoria": "Emociones", "fecha": "2026-06-02 20:30", "frase": ["estoy", "tranquilo"]},
    {"categoria": "Emociones", "fecha": "2026-06-02 21:00", "frase": ["necesito", "ayuda"]}
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

print("Datos de entrenamiento:")
print(datos_entrenamiento)

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

# joblib.dump(modelo, "modelo_base.pkl")
# joblib.dump(encoder_categoria, "encoder_categoria.pkl")
# joblib.dump(encoder_palabra, "encoder_palabra.pkl")

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