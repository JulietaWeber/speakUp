"""Dataset de frases de CAA (Comunicación Aumentativa y Alternativa) en español,
generado desde cero para el modelo de predicción por contexto de palabras.

A diferencia del dataset anterior (categoría + palabra -> palabra siguiente),
este dataset no usa categorías: cada frase es una secuencia de palabras que
una persona usuaria de un tablero de CAA podría ir tocando, y de cada frase
se extraen pares (contexto de hasta 3 palabras -> palabra siguiente) mediante
una ventana deslizante.

Se combinan:
- Plantillas combinatorias (verbo x objeto, persona, lugar, etc.) para cubrir
  muchísimas variantes reales de uso.
- Frases fijas curadas a mano para cubrir saludos, cortesía, emociones,
  salud, escuela, transporte, clima y vida diaria con lenguaje natural.
"""

# ── Vocabularios base ──────────────────────────────────────────────────────

VERBOS = [
    "comer", "tomar", "ver", "jugar", "leer", "escribir", "llamar", "usar", "pasear", "mostrar",
    "buscar", "llevar", "guardar", "pedir", "dar", "lavar", "limpiar", "abrir", "cerrar", "dibujar",
    "escuchar", "tocar", "armar", "pintar", "cocinar", "ayudar", "cuidar", "compartir", "prestar", "regalar",
    "estudiar", "practicar", "ordenar", "arreglar", "cargar",
]

OBJETOS = [
    "agua", "comida", "fruta", "pan", "leche", "jugo", "televisión", "película", "música", "libro",
    "cuaderno", "lápiz", "celular", "computadora", "juguete", "pelota", "mochila", "ropa", "zapatos", "puerta",
    "ventana", "luz", "perro", "gato", "mamá", "papá", "abuela", "abuelo", "hermano", "hermana",
    "amigo", "amiga", "maestra", "médico", "enfermera", "tarea", "dibujo", "cuento", "juego", "bicicleta",
    "auto", "colectivo", "remera", "pantalón", "campera", "cama", "almohada", "manta", "vaso", "plato",
]

PERSONAS = [
    "mamá", "papá", "abuela", "abuelo", "hermano", "hermana", "amigo", "amiga",
    "maestra", "médico", "enfermera", "tío", "tía", "primo", "prima", "psicóloga",
]

LUGARES = [
    "casa", "escuela", "parque", "baño", "cocina", "patio", "biblioteca", "hospital",
    "farmacia", "supermercado", "plaza", "playa", "club", "cine", "comedor", "jardín",
]

SINTOMAS = [
    "hambre", "sed", "sueño", "frío", "calor", "miedo", "fiebre", "náuseas",
    "mareos", "alergia", "tos", "gripe", "dolor", "picazón", "cansancio",
]

PARTES_CUERPO = [
    "cabeza", "estómago", "garganta", "oído", "brazo", "pierna", "espalda", "muela",
    "pie", "mano", "ojo", "cuello", "rodilla", "dedo", "nariz", "panza",
]

EMOCIONES = [
    "feliz", "triste", "enojado", "nervioso", "tranquilo", "cansado", "aburrido", "contento",
    "preocupado", "emocionado", "frustrado", "confundido", "orgulloso", "asustado", "sorprendido", "avergonzado",
]

ESTADOS_SENTIR = [
    "bien", "mal", "mejor", "peor", "solo", "acompañado", "nervioso", "tranquilo",
    "cansado", "confundido", "orgulloso", "incómodo",
]

VERBOS_NEGATIVOS = [
    "respirar", "caminar", "dormir", "comer", "hablar", "escuchar", "ver", "escribir", "leer", "moverme",
]

VERBOS_SIMPLES = [
    "comer", "dormir", "descansar", "jugar", "leer", "escribir", "dibujar", "cantar",
    "bailar", "saltar", "correr", "estudiar", "trabajar", "cocinar", "pasear", "nadar",
    "pintar", "construir", "aprender", "enseñar",
]

# ── Generación combinatoria de frases ──────────────────────────────────────

FRASES = []

for verbo in VERBOS:
    for objeto in OBJETOS:
        FRASES.append(["quiero", verbo, objeto])
        FRASES.append(["necesito", verbo, objeto])

for objeto in OBJETOS:
    FRASES.append(["quiero", objeto])
    FRASES.append(["necesito", objeto])

for verbo in VERBOS_SIMPLES:
    FRASES.append(["quiero", verbo])
    FRASES.append(["no", "quiero", verbo])
    FRASES.append(["hoy", "quiero", verbo])
    FRASES.append(["mañana", "quiero", verbo])

for verbo in VERBOS_NEGATIVOS:
    FRASES.append(["no", "puedo", verbo])
    FRASES.append(["no", "quiero", verbo])

for persona in PERSONAS:
    FRASES.append(["quiero", "hablar", "con", persona])
    FRASES.append(["quiero", "jugar", "con", persona])
    FRASES.append(["quiero", "llamar", "a", persona])
    FRASES.append(["extraño", "a", persona])
    FRASES.append(["quiero", "ver", "a", persona])
    FRASES.append(["necesito", "ayuda", "de", persona])

for verbo in VERBOS_SIMPLES:
    for lugar in LUGARES:
        FRASES.append(["quiero", verbo, "en", lugar])

for persona in PERSONAS:
    for objeto in OBJETOS[:20]:
        FRASES.append(["quiero", "dar", objeto, "a", persona])

for lugar in LUGARES:
    FRASES.append(["quiero", "ir", "a", lugar])
    FRASES.append(["necesito", "ir", "a", lugar])
    FRASES.append(["quiero", "volver", "a", lugar])
    FRASES.append(["estoy", "en", lugar])

for sintoma in SINTOMAS:
    FRASES.append(["tengo", sintoma])
    FRASES.append(["tengo", "mucho", sintoma])
    FRASES.append(["ya", "no", "tengo", sintoma])

for parte in PARTES_CUERPO:
    FRASES.append(["me", "duele", "la", parte])
    FRASES.append(["me", "duele", parte])

for emocion in EMOCIONES:
    FRASES.append(["estoy", emocion])
    FRASES.append(["hoy", "estoy", emocion])
    FRASES.append(["me", "siento", emocion])

for estado in ESTADOS_SENTIR:
    FRASES.append(["me", "siento", estado])
    FRASES.append(["hoy", "me", "siento", estado])

# ── Frases fijas curadas: vida diaria, saludos, cortesía, salud, escuela ────

FRASES_FIJAS = [
    # Saludos y cortesía
    ["hola", "cómo", "estás"],
    ["buenos", "días"],
    ["buenas", "tardes"],
    ["buenas", "noches"],
    ["gracias", "por", "ayudarme"],
    ["por", "favor", "ayudame"],
    ["de", "nada"],
    ["chau", "nos", "vemos", "pronto"],
    ["sí", "quiero"],
    ["no", "quiero", "eso"],
    ["disculpá", "la", "molestia"],
    ["perdón", "no", "quise", "molestar"],

    # Casa / vida diaria
    ["quiero", "ir", "al", "baño"],
    ["necesito", "ir", "al", "baño", "ahora"],
    ["quiero", "bañarme", "antes", "de", "dormir"],
    ["necesito", "cambiarme", "de", "ropa"],
    ["quiero", "ver", "televisión", "un", "rato"],
    ["quiero", "jugar", "un", "rato", "más"],
    ["necesito", "ayuda", "para", "vestirme"],
    ["quiero", "comer", "algo", "rico"],
    ["tengo", "hambre", "quiero", "comer", "ya"],
    ["tengo", "sed", "quiero", "tomar", "agua"],
    ["quiero", "dormir", "una", "siesta"],
    ["tengo", "sueño", "quiero", "ir", "a", "la", "cama"],
    ["necesito", "el", "cargador", "del", "celular"],
    ["apagá", "la", "luz", "por", "favor"],
    ["prendé", "la", "luz", "por", "favor"],
    ["cerrá", "la", "puerta", "por", "favor"],
    ["abrí", "la", "ventana", "por", "favor"],
    ["tengo", "frío", "necesito", "un", "abrigo"],
    ["tengo", "calor", "quiero", "tomar", "agua", "fría"],

    # Escuela
    ["no", "entiendo", "la", "consigna"],
    ["necesito", "ayuda", "con", "la", "tarea"],
    ["ya", "terminé", "la", "tarea"],
    ["quiero", "participar", "en", "la", "clase"],
    ["no", "quiero", "ir", "a", "la", "escuela", "hoy"],
    ["me", "gusta", "mucho", "la", "escuela"],
    ["perdí", "mi", "cuaderno", "de", "clase"],
    ["necesito", "un", "lápiz", "nuevo"],
    ["quiero", "hablar", "con", "la", "maestra"],
    ["tengo", "miedo", "de", "la", "prueba"],
    ["quiero", "trabajar", "en", "grupo"],
    ["me", "molesta", "el", "ruido", "en", "el", "aula"],
    ["quiero", "ir", "al", "recreo"],
    ["aprendí", "algo", "nuevo", "hoy"],
    ["quiero", "mostrar", "mi", "trabajo"],

    # Médico / salud
    ["me", "duele", "mucho", "la", "cabeza"],
    ["necesito", "un", "medicamento", "para", "el", "dolor"],
    ["me", "siento", "mejor", "que", "ayer"],
    ["me", "siento", "peor", "que", "antes"],
    ["necesito", "ir", "al", "médico", "ya"],
    ["tengo", "fiebre", "alta", "desde", "ayer"],
    ["no", "puedo", "respirar", "bien"],
    ["necesito", "mi", "inhalador", "ahora"],
    ["me", "lastimé", "el", "dedo", "jugando"],
    ["necesito", "una", "curita", "para", "la", "herida"],
    ["quiero", "que", "venga", "mamá", "al", "médico"],

    # Emociones
    ["estoy", "feliz", "porque", "vino", "mi", "amigo"],
    ["estoy", "triste", "porque", "perdí", "mi", "juguete"],
    ["estoy", "enojado", "porque", "me", "molestaron"],
    ["tengo", "miedo", "de", "la", "oscuridad"],
    ["necesito", "un", "abrazo", "por", "favor"],
    ["necesito", "calmarme", "un", "poco"],
    ["quiero", "llorar", "un", "momento"],
    ["extraño", "mucho", "a", "mi", "familia"],
    ["no", "quiero", "hablar", "ahora"],
    ["quiero", "hablar", "de", "lo", "que", "siento"],
    ["me", "da", "vergüenza", "contar", "esto"],

    # Transporte / clima
    ["espero", "el", "colectivo", "en", "la", "parada"],
    ["perdí", "el", "colectivo", "otra", "vez"],
    ["estoy", "perdido", "necesito", "ayuda", "para", "llegar"],
    ["cuánto", "falta", "para", "llegar"],
    ["hay", "mucho", "tráfico", "hoy"],
    ["está", "lloviendo", "necesito", "un", "paraguas"],
    ["quiero", "ir", "caminando", "hasta", "la", "plaza"],
    ["quiero", "ir", "en", "bicicleta", "al", "parque"],
    ["necesito", "cargar", "la", "tarjeta", "del", "colectivo"],
    ["llegamos", "a", "destino", "por", "fin"],

    # Amigos / social
    ["quiero", "jugar", "con", "mis", "amigos"],
    ["quiero", "salir", "con", "mis", "amigos", "hoy"],
    ["extraño", "mucho", "a", "mis", "amigos"],
    ["peleé", "con", "mi", "amigo", "hoy"],
    ["quiero", "pedir", "perdón", "a", "mi", "amigo"],
    ["mi", "amigo", "cumple", "años", "hoy"],
    ["quiero", "invitar", "a", "mi", "amigo", "a", "casa"],
    ["mi", "amigo", "me", "ayudó", "mucho"],
    ["mi", "amigo", "está", "triste", "hoy"],
    ["quiero", "hacer", "un", "nuevo", "amigo"],
    ["quiero", "sacarme", "una", "foto", "con", "mis", "amigos"],

    # Tecnología / entretenimiento
    ["quiero", "usar", "la", "computadora", "un", "rato"],
    ["quiero", "jugar", "videojuegos", "con", "mi", "hermano"],
    ["quiero", "escuchar", "música", "tranquila"],
    ["quiero", "ver", "una", "película", "de", "miedo"],
    ["quiero", "dibujar", "algo", "lindo"],
    ["quiero", "leer", "mi", "cuento", "favorito"],
]

FRASES.extend(FRASES_FIJAS)

# ── Ventana deslizante: contexto de hasta 3 palabras -> palabra siguiente ──

def generar_pares(frases):
    """Para cada frase, recorre cada posición y genera un par
    (contexto, siguiente) donde el contexto es una lista de hasta 3
    palabras inmediatamente anteriores (1, 2 o 3 según cuántas haya
    disponibles) y 'siguiente' es la palabra que sigue en la frase."""
    pares = []
    for frase in frases:
        palabras = [p.lower() for p in frase]
        for i in range(1, len(palabras)):
            contexto = palabras[max(0, i - 3):i]
            siguiente = palabras[i]
            pares.append((contexto, siguiente))
    return pares


PARES = generar_pares(FRASES)


if __name__ == "__main__":
    print(f"Frases totales: {len(FRASES)}")
    print(f"Pares generados (ventana deslizante 1-3 palabras): {len(PARES)}")
    print("Ejemplos:")
    for contexto, siguiente in PARES[:5]:
        print(f"  {contexto} -> {siguiente}")
