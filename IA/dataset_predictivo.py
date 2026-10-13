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
    "mirar", "cantar", "bailar", "correr", "saltar", "nadar", "trabajar", "manejar", "hornear",
    "coser", "tejer", "plantar", "regar", "barrer", "doblar", "colgar", "enchufar", "apagar",
    "prender", "subir", "bajar", "entrar", "salir", "esperar", "encontrar", "perder", "ganar",
    "agradecer", "saludar", "despedir", "abrazar", "besar", "peinar", "cepillar", "bañar", "vestir",
    "alimentar", "entrenar", "repasar", "revisar", "firmar", "enviar", "recibir", "comprar", "vender",
    "pagar", "reparar", "decorar", "organizar", "descansar", "respirar", "caminar", "estirar",
]

OBJETOS = [
    "agua", "comida", "fruta", "pan", "leche", "jugo", "televisión", "película", "música", "libro",
    "cuaderno", "lápiz", "celular", "computadora", "juguete", "pelota", "mochila", "ropa", "zapatos", "puerta",
    "ventana", "luz", "perro", "gato", "mamá", "papá", "abuela", "abuelo", "hermano", "hermana",
    "amigo", "amiga", "maestra", "médico", "enfermera", "tarea", "dibujo", "cuento", "juego", "bicicleta",
    "auto", "colectivo", "remera", "pantalón", "campera", "cama", "almohada", "manta", "vaso", "plato",
    "yogur", "queso", "huevo", "ensalada", "sopa", "pastel", "galletas", "chocolate", "caramelo", "helado",
    "café", "mate", "revista", "diario", "carpeta", "regla", "goma", "cartuchera", "gorra", "sombrero",
    "bufanda", "guantes", "medias", "zapatillas", "pijama", "toalla", "jabón", "peine", "espejo", "silla",
    "mesa", "sofá", "alfombra", "cortina", "radio", "parlante", "auriculares", "control", "tablet", "pila",
    "linterna", "paraguas", "patineta", "muñeca", "robot", "dado",
]

PERSONAS = [
    "mamá", "papá", "abuela", "abuelo", "hermano", "hermana", "amigo", "amiga",
    "maestra", "médico", "enfermera", "tío", "tía", "primo", "prima", "psicóloga",
    "vecino", "vecina", "compañero", "compañera", "entrenador", "entrenadora", "director", "directora",
    "bibliotecaria", "psicopedagoga", "terapeuta", "cuñado", "cuñada", "sobrino", "sobrina", "padrino", "madrina",
]

LUGARES = [
    "casa", "escuela", "parque", "baño", "cocina", "patio", "biblioteca", "hospital",
    "farmacia", "supermercado", "plaza", "playa", "club", "cine", "comedor", "jardín",
    "gimnasio", "iglesia", "museo", "teatro", "estadio", "shopping", "mercado", "dentista",
    "veterinaria", "peluquería", "trabajo", "oficina", "aeropuerto", "estación", "terminal", "vereda",
    "calle", "balcón", "terraza", "sótano", "garage", "quincho",
]

SINTOMAS = [
    "hambre", "sed", "sueño", "frío", "calor", "miedo", "fiebre", "náuseas",
    "mareos", "alergia", "tos", "gripe", "dolor", "picazón", "cansancio",
    "ardor", "escalofríos", "congestión", "vómito", "diarrea", "insomnio", "ansiedad", "estrés", "debilidad",
]

PARTES_CUERPO = [
    "cabeza", "estómago", "garganta", "oído", "brazo", "pierna", "espalda", "muela",
    "pie", "mano", "ojo", "cuello", "rodilla", "dedo", "nariz", "panza",
    "hombro", "codo", "muñeca", "cintura", "cadera", "tobillo", "talón", "ceja", "pestaña",
    "labio", "mentón", "frente", "mejilla", "uña",
]

EMOCIONES = [
    "feliz", "triste", "enojado", "nervioso", "tranquilo", "cansado", "aburrido", "contento",
    "preocupado", "emocionado", "frustrado", "confundido", "orgulloso", "asustado", "sorprendido", "avergonzado",
    "celoso", "culpable", "aliviado", "esperanzado", "decepcionado", "agradecido", "curioso", "inseguro",
    "valiente", "tímido",
]

ESTADOS_SENTIR = [
    "bien", "mal", "mejor", "peor", "solo", "acompañado", "nervioso", "tranquilo",
    "cansado", "confundido", "orgulloso", "incómodo",
    "fuerte", "débil", "relajado", "estresado", "motivado", "desmotivado", "seguro", "libre", "atrapado",
]

VERBOS_NEGATIVOS = [
    "respirar", "caminar", "dormir", "comer", "hablar", "escuchar", "ver", "escribir", "leer", "moverme",
    "pensar", "concentrarme", "recordar", "entender", "confiar", "parar",
]

VERBOS_SIMPLES = [
    "comer", "dormir", "descansar", "jugar", "leer", "escribir", "dibujar", "cantar",
    "bailar", "saltar", "correr", "estudiar", "trabajar", "cocinar", "pasear", "nadar",
    "pintar", "construir", "aprender", "enseñar",
    "viajar", "entrenar", "meditar", "relajarme", "divertirme", "concentrarme", "organizarme",
    "prepararme", "arreglarme", "ducharme",
]

ADJETIVOS = [
    "grande", "chico", "nuevo", "viejo", "lindo", "feo", "rico", "rápido", "lento", "fácil",
    "difícil", "importante", "divertido", "caro", "barato", "limpio", "sucio", "roto", "pesado", "liviano",
]

TIEMPO = [
    "hoy", "ahora", "mañana", "ayer", "luego", "después", "antes", "siempre", "nunca", "temprano", "tarde",
]

PREGUNTAS_INICIO = ["dónde", "cuándo", "cómo", "qué", "cuánto", "quién"]

# Subconjunto de objetos de uso muy frecuente y genérico, usado en patrones
# donde cualquier objeto puede aparecer (cantidad, negación, preguntas). Se
# usa un subconjunto chico (y no los ~95 OBJETOS completos) a propósito: así
# la ambigüedad de esos patrones queda acotada y predecible, en vez de
# repartirse casi uniformemente entre decenas de objetos posibles.
CORE_OBJETOS = [
    "agua", "comida", "leche", "jugo", "pan", "fruta", "televisión", "película",
    "música", "libro", "juguete", "pelota", "celular", "computadora", "ropa",
    "zapatos", "cama", "puerta", "luz", "perro", "gato", "mochila", "cuaderno",
    "lápiz", "tarea",
]

# Qué objetos tiene sentido pedir/usar con cada verbo. En vez de cruzar TODOS
# los verbos con TODOS los objetos (lo que generaría frases sin sentido como
# "quiero cerrar fruta" y, peor, haría que después de "quiero" pudiera venir
# casi cualquiera de ~90 verbos/objetos con probabilidad pareja, imposible de
# predecir), cada verbo se combina solo con objetos compatibles. Esto genera
# frases más naturales y una distribución de palabra-siguiente mucho más
# aprendible.
VERBO_OBJETOS = {
    "comer": ["pan", "fruta", "queso", "huevo", "ensalada", "sopa", "pastel", "galletas", "chocolate", "caramelo", "helado", "yogur"],
    "tomar": ["agua", "leche", "jugo", "café", "mate"],
    "ver": ["televisión", "película", "dibujo"],
    "jugar": ["juguete", "pelota", "muñeca", "robot", "dado"],
    "leer": ["libro", "cuento", "revista", "diario"],
    "escribir": ["cuaderno", "tarea", "cuento"],
    "escuchar": ["música", "radio"],
    "usar": ["celular", "computadora", "tablet", "control", "auriculares", "parlante"],
    "lavar": ["ropa", "plato", "vaso", "mochila"],
    "limpiar": ["mesa", "silla", "ventana", "alfombra", "cortina"],
    "abrir": ["puerta", "ventana"],
    "cerrar": ["puerta", "ventana"],
    "dibujar": ["dibujo"],
    "pintar": ["dibujo", "cuaderno"],
    "cocinar": ["sopa", "pastel", "ensalada"],
    "guardar": ["ropa", "juguete", "libro", "mochila", "celular"],
    "buscar": ["lápiz", "mochila", "celular", "zapatos", "juguete", "libro", "peine"],
    "llevar": ["mochila", "libro", "celular", "paraguas", "juguete", "toalla"],
    "mostrar": ["dibujo", "juguete", "cuento", "tarea"],
    "dar": ["agua", "comida", "juguete", "libro", "pelota"],
    "prestar": ["lápiz", "libro", "juguete", "celular", "goma"],
    "regalar": ["juguete", "libro", "chocolate", "caramelo", "pelota"],
    "cargar": ["celular", "mochila", "pila", "tablet"],
    "ordenar": ["ropa", "juguete", "cuaderno", "mesa"],
    "arreglar": ["bicicleta", "auto", "celular", "silla"],
    "vestir": ["ropa", "zapatillas", "campera", "remera", "pantalón"],
}

# Distintas formas en las que un usuario de CAA podría armar la misma idea
# (verbo + objeto). Multiplican la cantidad de frases sin introducir
# ambigüedad nueva: el objeto sigue acotado por el verbo en todos los casos.
PLANTILLAS_VERBO_OBJETO = [
    lambda v, o: ["quiero", v, o],
    lambda v, o: ["necesito", v, o],
    lambda v, o: ["quiero", v, o, "ahora"],
    lambda v, o: ["no", "quiero", v, o],
    lambda v, o: ["hoy", "quiero", v, o],
    lambda v, o: ["quiero", v, o, "por", "favor"],
    lambda v, o: ["puedo", v, o],
    lambda v, o: ["necesito", v, o, "ahora"],
    lambda v, o: ["mañana", "quiero", v, o],
]

# ── Generación combinatoria de frases ──────────────────────────────────────

FRASES = []

for verbo, objetos_compatibles in VERBO_OBJETOS.items():
    for objeto in objetos_compatibles:
        for plantilla in PLANTILLAS_VERBO_OBJETO:
            FRASES.append(plantilla(verbo, objeto))

for objeto in CORE_OBJETOS:
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
    for objeto in OBJETOS[:40]:
        FRASES.append(["quiero", "dar", objeto, "a", persona])

for lugar in LUGARES:
    FRASES.append(["quiero", "ir", "a", lugar])
    FRASES.append(["necesito", "ir", "a", lugar])
    FRASES.append(["quiero", "volver", "a", lugar])
    FRASES.append(["estoy", "en", lugar])
    FRASES.append(["quiero", "quedarme", "en", lugar])
    FRASES.append(["no", "quiero", "ir", "a", lugar])
    FRASES.append(["necesito", "volver", "a", lugar])
    FRASES.append(["quiero", "salir", "de", lugar])

for sintoma in SINTOMAS:
    FRASES.append(["tengo", sintoma])
    FRASES.append(["tengo", "mucho", sintoma])
    FRASES.append(["ya", "no", "tengo", sintoma])
    FRASES.append(["siento", sintoma])
    FRASES.append(["tengo", "poco", sintoma])
    FRASES.append(["todavía", "tengo", sintoma])

for parte in PARTES_CUERPO:
    FRASES.append(["me", "duele", "la", parte])
    FRASES.append(["me", "duele", parte])
    FRASES.append(["me", "duele", "mucho", "la", parte])
    FRASES.append(["tengo", "dolor", "en", "la", parte])
    FRASES.append(["me", "lastimé", "la", parte])

for emocion in EMOCIONES:
    FRASES.append(["estoy", emocion])
    FRASES.append(["hoy", "estoy", emocion])
    FRASES.append(["me", "siento", emocion])
    FRASES.append(["estoy", "muy", emocion])
    FRASES.append(["estoy", "un", "poco", emocion])
    FRASES.append(["ya", "no", "estoy", emocion])

for estado in ESTADOS_SENTIR:
    FRASES.append(["me", "siento", estado])
    FRASES.append(["hoy", "me", "siento", estado])

# ── Adjetivos: describir objetos ───────────────────────────────────────────

for objeto in CORE_OBJETOS:
    for adjetivo in ADJETIVOS[:10]:
        FRASES.append(["quiero", "un", objeto, adjetivo])

# ── Tiempo: cuándo quiero hacer algo ────────────────────────────────────────

for tiempo in TIEMPO:
    for verbo in VERBOS_SIMPLES:
        FRASES.append([tiempo, "quiero", verbo])
        FRASES.append([tiempo, "no", "quiero", verbo])
        FRASES.append([tiempo, "necesito", verbo])
        FRASES.append([tiempo, "puedo", verbo])

# ── Negaciones ampliadas ────────────────────────────────────────────────────

for verbo in VERBOS_SIMPLES:
    FRASES.append(["nunca", "quiero", verbo])
    FRASES.append(["ya", "no", "quiero", verbo])
    FRASES.append(["no", "puedo", verbo])
    FRASES.append(["no", "pude", verbo])

for objeto in CORE_OBJETOS:
    FRASES.append(["no", "quiero", objeto])
    FRASES.append(["no", "tengo", objeto])
    FRASES.append(["ya", "no", "quiero", objeto])

# ── Preguntas ────────────────────────────────────────────────────────────────

for objeto in CORE_OBJETOS:
    FRASES.append(["dónde", "está", objeto])
    FRASES.append(["quiero", "saber", "dónde", "está", objeto])

for persona in PERSONAS:
    FRASES.append(["dónde", "está", persona])
    FRASES.append(["cuándo", "viene", persona])

for lugar in LUGARES:
    FRASES.append(["cuándo", "vamos", "a", lugar])
    FRASES.append(["cómo", "llego", "a", lugar])

for verbo in VERBOS_SIMPLES:
    FRASES.append(["puedo", verbo])
    FRASES.append(["podemos", verbo])

# ── Cantidad ─────────────────────────────────────────────────────────────────

for objeto in CORE_OBJETOS:
    FRASES.append(["quiero", "más", objeto])
    FRASES.append(["quiero", "otro", objeto])
    FRASES.append(["no", "quiero", "más", objeto])
    FRASES.append(["quiero", "poco", objeto])
    FRASES.append(["perdí", "mi", objeto])
    FRASES.append(["encontré", "mi", objeto])
    FRASES.append(["rompí", "mi", objeto])
    FRASES.append(["traje", "mi", objeto])

# ── Persona + emoción / estado ──────────────────────────────────────────────

for persona in PERSONAS:
    for emocion in EMOCIONES:
        FRASES.append([persona, "está", emocion])
    for lugar in LUGARES:
        FRASES.append(["quiero", "ir", "con", persona, "a", lugar])

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

    # Rutina diaria
    ["quiero", "despertarme", "más", "tarde"],
    ["ya", "me", "desperté", "buenos", "días"],
    ["quiero", "desayunar", "antes", "de", "salir"],
    ["necesito", "cepillarme", "los", "dientes"],
    ["necesito", "peinarme", "antes", "de", "salir"],
    ["quiero", "ponerme", "las", "zapatillas"],
    ["ya", "estoy", "listo", "para", "salir"],
    ["quiero", "lavarme", "las", "manos"],
    ["necesito", "ir", "a", "dormir", "temprano"],
    ["quiero", "quedarme", "despierto", "un", "rato", "más"],

    # Mascotas
    ["quiero", "darle", "de", "comer", "al", "perro"],
    ["quiero", "sacar", "a", "pasear", "al", "perro"],
    ["quiero", "jugar", "con", "mi", "gato"],
    ["necesito", "llevar", "al", "perro", "al", "veterinario"],
    ["mi", "gato", "está", "enfermo"],
    ["quiero", "darle", "agua", "a", "mi", "perro"],
    ["mi", "perro", "quiere", "salir", "a", "pasear"],
    ["quiero", "bañar", "a", "mi", "perro"],

    # Celebraciones y familia
    ["hoy", "es", "mi", "cumpleaños"],
    ["quiero", "hacer", "una", "fiesta"],
    ["quiero", "invitar", "a", "toda", "la", "familia"],
    ["quiero", "comprar", "un", "regalo", "para", "mamá"],
    ["feliz", "cumpleaños", "para", "vos"],
    ["quiero", "soplar", "las", "velitas"],
    ["mañana", "es", "navidad", "estoy", "feliz"],
    ["quiero", "visitar", "a", "mis", "abuelos", "este", "fin", "de", "semana"],
    ["extraño", "a", "mi", "familia", "que", "vive", "lejos"],

    # Deportes / actividad física
    ["quiero", "jugar", "al", "fútbol", "con", "mis", "amigos"],
    ["quiero", "ir", "a", "nadar", "a", "la", "pileta"],
    ["quiero", "andar", "en", "bicicleta", "en", "el", "parque"],
    ["necesito", "practicar", "para", "el", "partido"],
    ["ganamos", "el", "partido", "estoy", "feliz"],
    ["perdimos", "el", "partido", "estoy", "triste"],
    ["quiero", "hacer", "ejercicio", "antes", "de", "comer"],
    ["estoy", "cansado", "después", "de", "entrenar"],

    # Trabajo / independencia
    ["quiero", "aprender", "a", "cocinar", "solo"],
    ["quiero", "ayudar", "a", "poner", "la", "mesa"],
    ["quiero", "guardar", "mi", "ropa", "en", "el", "placard"],
    ["necesito", "practicar", "para", "ser", "más", "independiente"],
    ["quiero", "manejar", "mi", "propio", "dinero"],
    ["quiero", "conseguir", "un", "trabajo", "algún", "día"],

    # Clima y estaciones
    ["hace", "mucho", "frío", "hoy"],
    ["hace", "mucho", "calor", "hoy"],
    ["está", "nublado", "no", "quiero", "salir"],
    ["hay", "sol", "quiero", "ir", "a", "la", "plaza"],
    ["está", "nevando", "quiero", "ver", "por", "la", "ventana"],
    ["hay", "viento", "fuerte", "hoy"],

    # Preguntas y pedidos cotidianos
    ["puedo", "ir", "al", "baño", "por", "favor"],
    ["puedo", "tomar", "agua", "por", "favor"],
    ["podés", "ayudarme", "con", "esto", "por", "favor"],
    ["qué", "vamos", "a", "comer", "hoy"],
    ["cuánto", "falta", "para", "comer"],
    ["quién", "me", "puede", "ayudar", "ahora"],
    ["por", "qué", "no", "puedo", "ir"],
    ["cómo", "se", "hace", "esto"],

    # Compras
    ["quiero", "comprar", "algo", "en", "el", "supermercado"],
    ["necesito", "plata", "para", "comprar", "comida"],
    ["cuánto", "cuesta", "esto", "por", "favor"],
    ["quiero", "pagar", "con", "tarjeta"],
    ["ya", "pagué", "vamos", "a", "casa"],
    ["necesito", "una", "bolsa", "para", "llevar", "las", "cosas"],
    ["quiero", "ver", "esa", "remera", "por", "favor"],
    ["no", "tengo", "plata", "suficiente"],

    # Permisos
    ["puedo", "salir", "un", "rato", "por", "favor"],
    ["puedo", "quedarme", "despierto", "un", "poco", "más"],
    ["me", "dejás", "ir", "a", "la", "plaza"],
    ["necesito", "permiso", "para", "salir"],
    ["puedo", "usar", "tu", "celular", "un", "momento"],
    ["puedo", "invitar", "a", "un", "amigo", "a", "casa"],

    # Horarios y planificación
    ["a", "qué", "hora", "vamos", "a", "salir"],
    ["a", "qué", "hora", "es", "la", "cena"],
    ["qué", "día", "es", "hoy"],
    ["mañana", "tengo", "clase", "temprano"],
    ["el", "fin", "de", "semana", "quiero", "descansar"],
    ["esta", "semana", "tengo", "mucha", "tarea"],
    ["quiero", "planear", "algo", "divertido", "para", "el", "sábado"],

    # Disculpas y elogios
    ["perdón", "no", "fue", "mi", "intención"],
    ["lo", "siento", "mucho", "de", "verdad"],
    ["fue", "mi", "culpa", "perdón"],
    ["hiciste", "un", "trabajo", "excelente"],
    ["te", "felicito", "por", "tu", "esfuerzo"],
    ["estoy", "orgulloso", "de", "vos"],
    ["gracias", "por", "entenderme"],
    ["te", "agradezco", "mucho", "la", "ayuda"],

    # Más vida diaria y cortesía
    ["buen", "provecho", "a", "todos"],
    ["que", "descanses", "esta", "noche"],
    ["que", "tengas", "un", "buen", "día"],
    ["nos", "vemos", "la", "próxima", "semana"],
    ["hasta", "luego", "nos", "vemos", "pronto"],
    ["bienvenido", "a", "mi", "casa"],
    ["pasá", "por", "favor", "adelante"],
    ["te", "quiero", "mucho", "mamá"],
    ["te", "quiero", "mucho", "papá"],
    ["quiero", "contarte", "algo", "importante"],
]

# Se repiten las frases curadas (cada una ya es una oración natural y
# específica, de baja ambigüedad) para que el modelo les dé más peso al
# entrenar frente a los patrones puramente combinatorios.
FRASES.extend(FRASES_FIJAS)
FRASES.extend(FRASES_FIJAS)
FRASES.extend(FRASES_FIJAS)
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
