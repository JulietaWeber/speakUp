import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))              # IA/scripts/datos
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))     # IA/

# Concordancia (artículos, adjetivos, verbos) con las mismas reglas que usa el
# corrector en producción: las frases del corpus tienen que ser correctas.
from morfologia import (  # noqa: E402
    FEMENINAS_A_TONICA, conjugar, flexionar_determinante, formas_adjetivo, pluralizar,
)

# Frases correctas de CAA en español rioplatense. Son la base de los dos
# modelos: entrenar_prediccion.py cuenta sus n-gramas y entrenar_correccion.py
# las rompe a propósito para enseñarle al corrector a repararlas.
SALIDA = os.path.join(AQUI, "corpus_caa.txt")
CANTIDAD = 45000

# ── Léxico ────────────────────────────────────────────────────────────────────
# (palabra, género, tipo) - tipo: "masa" (se usa sin artículo: "tomar agua"),
# "cont" (contable: "una manzana") o "pl" (se usa en plural: "fideos").

COMIDAS = [
    ("pizza", "f", "masa"), ("pan", "m", "masa"), ("fruta", "f", "masa"), ("sopa", "f", "masa"),
    ("arroz", "m", "masa"), ("pollo", "m", "masa"), ("carne", "f", "masa"), ("ensalada", "f", "masa"),
    ("queso", "m", "masa"), ("helado", "m", "cont"), ("manzana", "f", "cont"), ("banana", "f", "cont"),
    ("naranja", "f", "cont"), ("pera", "f", "cont"), ("torta", "f", "masa"), ("chocolate", "m", "masa"),
    ("yogur", "m", "cont"), ("sándwich", "m", "cont"), ("hamburguesa", "f", "cont"),
    ("empanada", "f", "cont"), ("milanesa", "f", "cont"), ("tostada", "f", "cont"),
    ("galletita", "f", "cont"), ("caramelo", "m", "cont"), ("fideos", "m", "pl"),
    ("papas fritas", "f", "pl"), ("cereales", "m", "pl"), ("uvas", "f", "pl"), ("huevo", "m", "cont"),
    ("flan", "m", "cont"), ("puré", "m", "masa"), ("postre", "m", "cont"), ("alfajor", "m", "cont"),
    ("medialuna", "f", "cont"), ("tarta", "f", "masa"), ("pochoclos", "m", "pl"),
    ("ravioles", "m", "pl"), ("guiso", "m", "masa"), ("mandarina", "f", "cont"),
    ("frutillas", "f", "pl"), ("salchicha", "f", "cont"), ("panchos", "m", "pl"),
]
SABORES = {
    "helado": ["de chocolate", "de frutilla", "de dulce de leche", "de vainilla"],
    "torta": ["de chocolate", "de cumpleaños", "de vainilla"],
    "empanada": ["de carne", "de pollo", "de jamón y queso"],
    "sándwich": ["de jamón y queso", "de milanesa"],
    "tarta": ["de verdura", "de jamón y queso"],
    "galletita": ["de chocolate", "de agua"],
    "yogur": ["de frutilla", "con cereales"],
    "flan": ["con dulce de leche"],
}
BEBIDAS = [
    ("agua", "f", "masa"), ("leche", "f", "masa"), ("jugo", "m", "masa"), ("chocolatada", "f", "masa"),
    ("mate", "m", "masa"), ("té", "m", "masa"), ("gaseosa", "f", "masa"), ("licuado", "m", "cont"),
    ("café", "m", "masa"),
]
ADJ_COMIDA = ["rico", "caliente", "frío", "dulce", "grande", "chico", "casero", "fresco"]
ADJ_BEBIDA = ["frío", "caliente", "fresco", "rico"]

OBJETOS = [
    ("pelota", "f"), ("juguete", "m"), ("libro", "m"), ("cuaderno", "m"), ("lápiz", "m"),
    ("mochila", "f"), ("celular", "m"), ("tablet", "f"), ("computadora", "f"), ("campera", "f"),
    ("remera", "f"), ("pantalón", "m"), ("gorra", "f"), ("buzo", "m"), ("pijama", "m"),
    ("toalla", "f"), ("cepillo", "m"), ("vaso", "m"), ("plato", "m"), ("cuchara", "f"),
    ("silla", "f"), ("almohada", "f"), ("manta", "f"), ("frazada", "f"), ("llave", "f"),
    ("bicicleta", "f"), ("muñeca", "f"), ("muñeco", "m"), ("dibujo", "m"), ("cuento", "m"),
    ("auto", "m"), ("autito", "m"), ("cartuchera", "f"), ("goma", "f"), ("regla", "f"),
    ("tijera", "f"), ("carpeta", "f"), ("globo", "m"), ("peluche", "m"), ("control", "m"),
    ("botella", "f"), ("reloj", "m"), ("monopatín", "m"), ("patineta", "f"), ("pulsera", "f"),
    ("collar", "m"), ("cargador", "m"), ("vestido", "m"), ("pollera", "f"), ("bufanda", "f"),
    ("caja", "f"), ("tele", "f"), ("radio", "f"), ("ventana", "f"), ("puerta", "f"), ("luz", "f"),
    ("cama", "f"), ("mesa", "f"), ("taza", "f"), ("valija", "f"), ("bolsa", "f"), ("foto", "f"),
]
OBJETOS_PL = [("zapatillas", "f"), ("zapatos", "m"), ("medias", "f"), ("anteojos", "m"),
              ("auriculares", "m"), ("crayones", "m"), ("lápices", "m"), ("bloques", "m"),
              ("guantes", "m"), ("botas", "f"), ("figuritas", "f"), ("ojotas", "f")]
ADJ_OBJ = ["nuevo", "viejo", "rojo", "azul", "verde", "amarillo", "negro", "blanco", "rosa",
           "grande", "chico", "lindo", "favorito", "roto", "sucio", "limpio", "pesado", "largo",
           "mojado", "lleno", "vacío", "violeta", "naranja", "celeste", "gris", "marrón"]

# Lugares: (palabra, género) o artículo especial ("casa" va sin artículo).
LUGARES = [
    ("escuela", "f"), ("parque", "m"), ("plaza", "f"), ("baño", "m"), ("cocina", "f"),
    ("pieza", "f"), ("patio", "m"), ("hospital", "m"), ("club", "m"), ("cine", "m"),
    ("playa", "f"), ("pileta", "f"), ("supermercado", "m"), ("kiosco", "m"), ("farmacia", "f"),
    ("biblioteca", "f"), ("heladería", "f"), ("campo", "m"), ("shopping", "m"),
    ("consultorio", "m"), ("colegio", "m"), ("comedor", "m"), ("living", "m"), ("jardín", "m"),
    ("zoológico", "m"), ("museo", "m"), ("vereda", "f"), ("calesita", "f"), ("panadería", "f"),
    ("verdulería", "f"), ("peluquería", "f"), ("iglesia", "f"), ("estación", "f"), ("aula", "f"),
    ("gimnasio", "m"), ("terraza", "f"), ("balcón", "m"), ("quinta", "f"), ("dentista", "m"),
    ("médico", "m"), ("pediatra", "m"),
]
LUGARES_EN = [l for l in LUGARES if l[0] not in ("dentista", "médico", "pediatra")]
EVENTOS = [
    "el cumpleaños de mi primo", "el cumpleaños de mi amiga", "la fiesta de la escuela",
    "el acto de la escuela", "la casa de mi abuela", "la casa de mi amigo", "la casa de mi tía",
    "lo de mi abuela", "la clase de natación", "la clase de música", "el turno con el médico",
]

# Personas del entorno: con "mi" (familia) o con artículo (profesionales).
FAMILIA = [
    ("mamá", "f"), ("papá", "m"), ("hermano", "m"), ("hermana", "f"), ("abuela", "f"),
    ("abuelo", "m"), ("tío", "m"), ("tía", "f"), ("primo", "m"), ("prima", "f"), ("amigo", "m"),
    ("amiga", "f"), ("vecino", "m"), ("vecina", "f"), ("padrino", "m"), ("madrina", "f"),
    ("compañero", "m"), ("compañera", "f"), ("perro", "m"), ("gato", "m"), ("perrita", "f"),
]
FAMILIA_PL = [("amigos", "m"), ("primos", "m"), ("abuelos", "m"), ("hermanos", "m"),
              ("compañeros", "m"), ("tíos", "m"), ("papás", "m"), ("amigas", "f"), ("primas", "f")]
PROFESIONALES = [
    ("maestra", "f"), ("maestro", "m"), ("seño", "f"), ("profe", "m"), ("doctora", "f"),
    ("médico", "m"), ("psicóloga", "f"), ("terapeuta", "f"), ("enfermera", "f"), ("chofer", "m"),
    ("fonoaudióloga", "f"), ("kinesiólogo", "m"), ("directora", "f"), ("portero", "m"),
    ("acompañante", "f"), ("dentista", "m"),
]

CUERPO = [
    ("cabeza", "f"), ("panza", "f"), ("estómago", "m"), ("garganta", "f"), ("muela", "f"),
    ("oído", "m"), ("ojo", "m"), ("pierna", "f"), ("brazo", "m"), ("mano", "f"), ("pie", "m"),
    ("espalda", "f"), ("rodilla", "f"), ("dedo", "m"), ("diente", "m"), ("nariz", "f"),
    ("cuello", "m"), ("oreja", "f"), ("tobillo", "m"), ("hombro", "m"), ("codo", "m"),
    ("muñeca", "f"), ("pecho", "m"), ("cola", "f"),
]
CUERPO_PL_OK = {"oído", "ojo", "pierna", "brazo", "mano", "pie", "diente", "muela", "rodilla", "dedo", "oreja"}

ESTADOS = [
    "cansado", "contento", "triste", "enojado", "nervioso", "aburrido", "asustado", "preocupado",
    "emocionado", "tranquilo", "enfermo", "mojado", "sucio", "listo", "solo", "feliz", "mejor",
    "orgulloso", "confundido", "dormido", "despierto", "lleno", "celoso", "frustrado",
    "resfriado", "mareado", "ocupado", "cómodo", "incómodo", "sorprendido", "apurado", "perdido",
    "calmado", "ansioso", "molesto", "agotado", "lastimado", "contento",
]
ADJ_SER = ["bueno", "alto", "bajo", "divertido", "lindo", "inteligente", "amable", "gracioso",
           "simpático", "cariñoso", "valiente", "tímido", "rápido", "fuerte", "grande", "chico"]

SENSACIONES = [("hambre", "f"), ("sed", "f"), ("frío", "m"), ("calor", "m"), ("sueño", "m"),
               ("miedo", "m"), ("fiebre", "f"), ("tos", "f"), ("vergüenza", "f"),
               ("cosquillas", "f", "p"), ("mocos", "m", "p"), ("náuseas", "f", "p")]

TIEMPO_PRES = ["hoy", "ahora", "a la tarde", "a la noche", "después", "más tarde", "esta tarde",
               "todos los días", "siempre", "a veces", "a la mañana", "otra vez", "un rato"]
TIEMPO_PAS = ["ayer", "hoy", "anoche", "el sábado", "el domingo", "esta mañana",
              "la semana pasada", "el fin de semana", "el otro día", "recién", "hoy en la escuela"]
TIEMPO_FUT = ["mañana", "el sábado", "el domingo", "esta tarde", "después", "más tarde",
              "el fin de semana", "la semana que viene", "a la noche", "pasado mañana", "el lunes"]

CLIMA = ["hace frío", "hace calor", "llueve", "está lloviendo", "hay sol", "está nublado",
         "hace mucho viento", "hace mucho frío", "hace mucho calor", "va a llover"]

REFLEXIVO = {"1s": "me", "2s": "te", "2v": "te", "3s": "se", "1p": "nos", "3p": "se"}
DATIVO = {"1s": "me", "2s": "te", "2v": "te", "3s": "le", "1p": "nos", "3p": "les"}
POSESIVO = {"1s": "mi", "2s": "tu", "2v": "tu", "3s": "su", "1p": "nuestro", "3p": "su"}

# ── Ayudas de armado ──────────────────────────────────────────────────────────

ch = random.choice


def det(tipo, genero, numero, sustantivo):
    """Determinante concordado: det('def', 'f', 's', 'agua') -> 'el'."""
    base = {"def": "el", "indef": "un", "este": "este", "ese": "ese", "mucho": "mucho",
            "otro": "otro", "poco": "poco", "todo": "todo", "mi": "mi", "tu": "tu", "su": "su",
            "nuestro": "nuestro", "alguno": "algún", "ninguno": "ningún"}[tipo]
    primera = sustantivo.split()[0]
    return flexionar_determinante(base, genero, numero, primera)


def adj(base, genero, numero):
    return formas_adjetivo(base)[(genero, numero)]


def sintagma(palabra, genero, tipo_det, numero="s", adjetivo=None, plural_dado=False):
    """'una remera roja', 'las zapatillas nuevas', 'mi perro', 'agua fría'."""
    sust = palabra if (numero == "s" or plural_dado) else pluralizar(palabra)
    partes = []
    if tipo_det:
        partes.append(det(tipo_det, genero, numero, sust))
    partes.append(sust)
    if adjetivo:
        partes.append(adj(adjetivo, genero, numero))
    return " ".join(partes)


def prep(p, frase):
    """Contracciones: prep('a', 'el parque') -> 'al parque'."""
    if p in ("a", "de") and frase.startswith("el "):
        return p + "l " + frase[3:]
    return p + " " + frase


# Sintagmas al azar ya concordados: "unas empanadas de carne", "agua fría",
# "un vaso de jugo", "mi mochila nueva", "la maestra", "a la plaza"...
def comida(con_adj=0.25):
    palabra, g, tipo = ch(COMIDAS)
    sabor = ""
    if palabra in SABORES and random.random() < 0.4:
        sabor = " " + ch(SABORES[palabra])
    if tipo == "pl":
        d = ch([None, None, "def", "indef", "mucho", "poco"])
        return sintagma(palabra, g, d, "p", plural_dado=True) + sabor
    if tipo == "masa":
        d = ch([None, None, None, "def", "mucho", "poco"])
        a = ch(ADJ_COMIDA) if random.random() < con_adj and not sabor else None
        if d in ("mucho", "poco") and palabra in ("pizza", "torta", "tarta"):
            d = None
        return sintagma(palabra, g, d, "s", a) + sabor
    numero = "p" if random.random() < 0.3 else "s"
    d = ch(["indef", "indef", "def", "otro"] + (["mucho", None] if numero == "p" else []))
    a = ch(ADJ_COMIDA) if random.random() < con_adj and not sabor else None
    return sintagma(palabra, g, d, numero, a) + sabor


def bebida():
    palabra, g, tipo = ch(BEBIDAS)
    r = random.random()
    if r < 0.45:
        a = ch(ADJ_BEBIDA) if random.random() < 0.35 else None
        return sintagma(palabra, g, None, "s", a)
    if r < 0.65:
        return ch(["un vaso de ", "una taza de ", "una botella de ", "un poco de ", "más "]) + palabra
    if r < 0.8 and palabra == "jugo":
        return "jugo de " + ch(["naranja", "manzana", "durazno", "pera"])
    return sintagma(palabra, g, ch(["def", "mucho"]), "s")


def objeto(tipos=("def", "indef", "mi", "este"), numero=None, adjetivo=0.3, pos=None):
    if numero == "p" or (numero is None and random.random() < 0.2):
        palabra, g = ch(OBJETOS_PL)
        tipo = ch(tipos)
        if tipo == "mi" and pos:
            tipo = pos
        a = ch(ADJ_OBJ) if random.random() < adjetivo else None
        return sintagma(palabra, g, tipo, "p", a, plural_dado=True)
    palabra, g = ch(OBJETOS)
    tipo = ch(tipos)
    if tipo == "mi" and pos:
        tipo = pos
    a = ch(ADJ_OBJ) if random.random() < adjetivo else None
    return sintagma(palabra, g, tipo, "s", a)


def persona(plural=None):
    """'mi mamá', 'la maestra', 'mis amigos'."""
    r = random.random()
    if plural or (plural is None and r < 0.15):
        palabra, g = ch(FAMILIA_PL)
        if palabra == "papás":
            return "mis papás"
        d = ch(["mis ", "mis ", "los "])
        return ("las " if d == "los " and g == "f" else d) + palabra
    if r < 0.75:
        palabra, g = ch(FAMILIA)
        return "mi " + palabra
    palabra, g = ch(PROFESIONALES)
    return det("def", g, "s", palabra) + " " + palabra


def a_persona(plural=None):
    return prep("a", persona(plural))


def con_persona():
    return "con " + persona()


def lugar_articulado(lugares=LUGARES):
    palabra, g = ch(lugares)
    return det("def", g, "s", palabra) + " " + palabra


def a_lugar():
    r = random.random()
    if r < 0.12:
        return ch(["a casa", "a mi casa", "a la casa de mi abuela", "a lo de mi abuela", "a terapia"])
    if r < 0.2:
        return prep("a", ch(EVENTOS))
    return prep("a", lugar_articulado())


def en_lugar():
    if random.random() < 0.12:
        return ch(["en casa", "en mi casa", "en la casa de mi tía", "en lo de mi abuela"])
    return "en " + lugar_articulado(LUGARES_EN)


def tiempo(lista):
    return ch(lista)


def juego():
    return ch([
        "a la pelota", "al fútbol", "a las escondidas", "a la mancha", "con los autitos",
        "con la tablet", "con mis muñecas", "a los videojuegos", "con la plastilina",
        "con mis amigos", "con mi hermano", "con el perro", "a las cartas", "al básquet",
        "con los bloques", "a la play", "en el patio", "en la plaza", "con mi prima",
        "al ajedrez", "con agua", "a un juego de mesa",
    ])


# Actividades: infinitivo -> complementos posibles. Los reflexivos terminan
# en "se" ("bañarse") y el clítico se ajusta a la persona del sujeto.
ACTIVIDADES = {
    "comer": [comida, comida, lambda: comida() + " " + con_persona(), lambda: "algo rico",
              lambda: comida() + " de postre", lambda: ""],
    "tomar": [bebida, bebida, lambda: "la leche", lambda: "la merienda", lambda: "el remedio",
              lambda: "el colectivo", lambda: "un helado"],
    "ver": [lambda: "la tele", lambda: "una película", lambda: "dibujitos", lambda: "una serie",
            lambda: "videos en la tablet", lambda: "el partido", a_persona,
            lambda: "una película " + con_persona()],
    "jugar": [juego, juego, lambda: juego() + " " + en_lugar(), con_persona],
    "escuchar": [lambda: "música", lambda: "un cuento", lambda: "la radio", lambda: "una canción",
                 lambda: "música tranquila", lambda: "música con los auriculares"],
    "leer": [lambda: "un libro", lambda: "un cuento", lambda: "una revista",
             lambda: "mi libro favorito", lambda: "un cuento " + con_persona()],
    "dibujar": [lambda: "una casa", lambda: "un perro", lambda: "una flor", lambda: "un dibujo",
                lambda: "con los crayones", lambda: "con los lápices de colores", lambda: ""],
    "pintar": [lambda: "un dibujo", lambda: "con témperas", lambda: "la caja",
               lambda: "un dibujo para " + persona()],
    "ir": [a_lugar, a_lugar, lambda: a_lugar() + " " + con_persona()],
    "dormir": [lambda: "la siesta", lambda: "un rato", lambda: "", lambda: "temprano",
               lambda: con_persona()],
    "bañarse": [lambda: "", lambda: "antes de dormir", lambda: "con agua caliente"],
    "cambiarse": [lambda: "de ropa", lambda: "", lambda: "la remera"],
    "lavarse": [lambda: "las manos", lambda: "los dientes", lambda: "la cara", lambda: "el pelo"],
    "cepillarse": [lambda: "los dientes", lambda: "el pelo"],
    "salir": [lambda: "al patio", lambda: "a la vereda", lambda: "a pasear", lambda: "a jugar",
              con_persona, lambda: "a la calle"],
    "andar": [lambda: "en bicicleta", lambda: "en monopatín", lambda: "en patineta",
              lambda: "a caballo"],
    "nadar": [lambda: "en la pileta", lambda: "en el mar", lambda: "", lambda: "en el club"],
    "hacer": [lambda: "la tarea", lambda: "una torta", lambda: "ejercicio", lambda: "un dibujo",
              lambda: "la cama", lambda: "un regalo para " + persona()],
    "armar": [lambda: "un rompecabezas", lambda: "un castillo", lambda: "una torre con los bloques",
              lambda: "la mochila"],
    "cocinar": [lambda: "una torta", lambda: "galletitas", lambda: "fideos", con_persona,
                lambda: "una pizza"],
    "comprar": [comida, lambda: objeto(("indef",)), lambda: "caramelos",
                lambda: "un regalo para " + persona(), lambda: "figuritas"],
    "buscar": [lambda: objeto(("def", "mi")), a_persona, lambda: "mi mochila"],
    "usar": [lambda: "la computadora", lambda: "la tablet", lambda: "el celular",
             lambda: "los auriculares", lambda: "el baño"],
    "descansar": [lambda: "", lambda: "un rato", lambda: "en la cama"],
    "merendar": [lambda: "tostadas", lambda: "galletitas", lambda: "", lambda: "una chocolatada"],
    "almorzar": [lambda: "", lambda: "milanesas con puré", lambda: "fideos", lambda: con_persona()],
    "cenar": [lambda: "", lambda: "pizza", lambda: "empanadas", lambda: con_persona()],
    "desayunar": [lambda: "", lambda: "cereales", lambda: "tostadas con manteca", lambda: "un yogur"],
    "hablar": [con_persona, lambda: "por teléfono", lambda: "con la maestra",
               lambda: "con mi mamá por teléfono"],
    "llamar": [a_persona, lambda: "por teléfono " + a_persona()],
    "visitar": [a_persona, lambda: "a mis abuelos"],
    "abrazar": [a_persona],
    "correr": [lambda: "en el patio", lambda: "en la plaza", lambda: "", lambda: "rápido"],
    "pasear": [lambda: "al perro", lambda: "por la plaza", lambda: ""],
    "ordenar": [lambda: "mi pieza", lambda: "los juguetes", lambda: "la mochila"],
    "poner": [lambda: "la mesa", lambda: "la música más fuerte"],
    "ayudar": [a_persona, lambda: "a mi mamá en la cocina"],
    "estudiar": [lambda: "para la prueba", lambda: "matemática", lambda: "", lambda: "inglés"],
    "escribir": [lambda: "mi nombre", lambda: "un cuento", lambda: "en el cuaderno",
                 lambda: "una carta para " + persona()],
    "cantar": [lambda: "una canción", lambda: "", lambda: "con mis amigos"],
    "bailar": [lambda: "", con_persona, lambda: "en la fiesta"],
    "saltar": [lambda: "en la cama elástica", lambda: "la soga", lambda: ""],
    "sentarse": [lambda: "", lambda: "en la silla", lambda: "al lado de mi amigo",
                 lambda: "en el sillón"],
    "acostarse": [lambda: "", lambda: "temprano", lambda: "un rato"],
    "quedarse": [lambda: "en casa", lambda: con_persona(), lambda: "un rato más",
                 lambda: en_lugar()],
    "volver": [lambda: "a casa", a_lugar],
    "subir": [lambda: "al colectivo", lambda: "las escaleras", lambda: "al auto"],
    "bajar": [lambda: "del colectivo", lambda: "las escaleras", lambda: "del auto"],
    "abrir": [lambda: "la ventana", lambda: "la puerta", lambda: "el regalo", lambda: "la heladera"],
    "cerrar": [lambda: "la puerta", lambda: "la ventana", lambda: "la canilla"],
    "prender": [lambda: "la luz", lambda: "la tele", lambda: "el ventilador", lambda: "la estufa"],
    "apagar": [lambda: "la luz", lambda: "la tele", lambda: "la computadora"],
    "regar": [lambda: "las plantas"],
    "cuidar": [lambda: "a mi hermano", lambda: "al perro", lambda: "las plantas"],
    "esperar": [lambda: "el colectivo", a_persona, lambda: "un ratito"],
    "aprender": [lambda: "a nadar", lambda: "a leer", lambda: "a andar en bicicleta",
                 lambda: "inglés"],
    "pedir": [lambda: "ayuda", lambda: "perdón", lambda: "un helado"],
    "mirar": [lambda: "la tele", lambda: "por la ventana", lambda: "las fotos"],
    "traer": [lambda: objeto(("mi",)), lambda: "la pelota"],
    "llevar": [lambda: objeto(("mi", "def")), lambda: "el perro al veterinario"],
    "romper": [lambda: objeto(("mi", "def"))],
    "perder": [lambda: objeto(("mi",))],
    "encontrar": [lambda: objeto(("mi",))],
    "terminar": [lambda: "la tarea", lambda: "la comida"],
    "probar": [lambda: comida(), lambda: "la comida"],
    "festejar": [lambda: "mi cumpleaños", lambda: "el cumpleaños de mi hermano"],
}
VERBOS_ACCION = list(ACTIVIDADES)

# ── Sujetos ───────────────────────────────────────────────────────────────────


def sujeto(hablante, pesos_1s=0.55):
    """(texto, persona, género, número) del sujeto de la oración."""
    if random.random() < pesos_1s:
        return (ch(["", "", "", "yo"]), "1s", hablante, "s")
    r = random.random()
    if r < 0.3:
        palabra, g = ch(FAMILIA)
        return ("mi " + palabra, "3s", g, "s")
    if r < 0.42:
        palabra, g = ch(PROFESIONALES)
        return (det("def", g, "s", palabra) + " " + palabra, "3s", g, "s")
    if r < 0.58:
        palabra, g = ch(FAMILIA_PL)
        return (("mis " if palabra != "papás" else "mis ") + palabra, "3p", g, "p")
    if r < 0.66:
        return (ch(["los chicos", "las chicas", "ellos", "ellas", "ustedes"]), "3p",
                "f" if random.random() < 0.3 else "m", "p")
    if r < 0.8:
        return (ch(["", "nosotros", "mi hermano y yo", "mi mamá y yo"]), "1p", "m", "p")
    if r < 0.92:
        return (ch(["vos", ""]), "2v", ch("mf"), "s")
    return (ch(["él", "ella"]), "3s", "m", "s") if random.random() < 0.5 else ("ella", "3s", "f", "s")


def _ajustar_genero_pronombre(s):
    texto, per, g, n = s
    if texto in ("ella", "ellas", "las chicas"):
        g = "f"
    if texto in ("él", "ellos", "los chicos"):
        g = "m"
    return texto, per, g, n


def con_sujeto(s, verbo):
    texto = s[0]
    return f"{texto} {verbo}".strip()


def infinitivo(verbo, persona):
    """'bañarse' + '1s' -> 'bañarme'."""
    if verbo.endswith("se"):
        return verbo[:-2] + REFLEXIVO[persona]
    return verbo


def conj(verbo, tiempo_v, persona):
    """Forma conjugada, con el clítico adelante si es reflexivo."""
    if verbo.endswith("se"):
        return REFLEXIVO[persona] + " " + conjugar(verbo[:-2], tiempo_v, persona)
    return conjugar(verbo, tiempo_v, persona)


def complemento(verbo):
    return ch(ACTIVIDADES[verbo])()


def actividad_inf(persona_s):
    v = ch(VERBOS_ACCION)
    return " ".join(x for x in (infinitivo(v, persona_s), complemento(v)) if x)


def unir(*partes):
    return " ".join(p for p in partes if p)


def oracion(texto, pregunta=False, exclamacion=False):
    # mayúscula inicial y "¿...?", "¡...!" o punto final
    texto = " ".join(texto.split())
    texto = texto.replace(" ,", ",")
    if pregunta:
        return "¿" + texto[0].upper() + texto[1:] + "?"
    if exclamacion:
        return "¡" + texto[0].upper() + texto[1:] + "!"
    return texto[0].upper() + texto[1:] + "."


def con_tiempo(clausula, lista, prob=0.35):
    # a veces agrega un tiempo ("hoy", "ayer"...) al principio o al final
    if random.random() >= prob:
        return clausula
    t = tiempo(lista)
    if random.random() < 0.6:
        return t + " " + clausula
    return clausula + " " + t


# ── Cláusulas ─────────────────────────────────────────────────────────────────
# Cada cl_* arma una cláusula (sin mayúscula ni punto) con el verbo conjugado
# según su sujeto: "mis amigos juegan", "vos querés", "quiero bañarme".


def cl_deseo(hablante):
    s = _ajustar_genero_pronombre(sujeto(hablante))
    per = s[1]
    modal = ch(["querer", "querer", "querer", "necesitar", "poder", "tener ganas de", "tener que",
                "ir a", "preferir", "gustar"])
    neg = "no " if random.random() < 0.18 else ""
    act = actividad_inf(per)
    if modal == "gustar":
        a = {"1s": "", "2v": "a vos", "1p": "a nosotros", "3p": "a " + s[0] if s[0] else ""}
        pre = a.get(per, ("a " + s[0]) if s[0] else "")
        pre = prep("a", s[0]) if per in ("3s", "3p") and s[0] else pre
        if per in ("3s", "3p") and not s[0]:
            pre = ""
        return unir(pre, neg + DATIVO[per], ch(["gusta", "gustaría"]), act)
    if modal in ("tener ganas de", "tener que", "ir a"):
        verbo, resto = modal.split(" ", 1)
        return con_tiempo(unir(s[0], neg + conjugar(verbo, "pres", per), resto, act), TIEMPO_FUT)
    tiempo_v = "cond" if (modal == "querer" and random.random() < 0.1) else "pres"
    return con_tiempo(unir(s[0], neg + conjugar(modal, tiempo_v, per), act), TIEMPO_PRES + TIEMPO_FUT)


def cl_estado(hablante):
    s = _ajustar_genero_pronombre(sujeto(hablante, 0.6))
    texto, per, g, n = s
    neg = "no " if random.random() < 0.1 else ""
    intens = ch(["", "", "", "muy ", "un poco ", "re ", "tan "])
    if intens == "tan ":
        intens = ""
    a = adj(ch(ESTADOS), g, n)
    t = ch(["pres", "pres", "pres", "pret", "imp"])
    if random.random() < 0.15:
        verbo = conj("sentirse", t, per)
    else:
        verbo = conjugar("estar", t, per)
    lista = ["hoy", "ahora", "un poco"] if t == "pres" else ["ayer", "anoche", "hoy en la escuela", "el sábado"]
    if intens == "un poco ":
        lista = [x for x in lista if x != "un poco"]
    return con_tiempo(unir(texto, neg + verbo, intens + a), lista, 0.25)


def cl_ser(hablante):
    """'Mi perro es muy grande', 'La sopa está fría', 'Las zapatillas están rotas'."""
    r = random.random()
    if r < 0.4:
        palabra, g = ch(OBJETOS + OBJETOS_PL)
        n = "p" if (palabra, g) in OBJETOS_PL else ("p" if random.random() < 0.2 else "s")
        sust = palabra if (palabra, g) in OBJETOS_PL or n == "s" else pluralizar(palabra)
        d = ch(["def", "mi", "este", "tu"])
        de_alguien = random.random() < 0.2
        if de_alguien:
            d = "def"
        sujeto_txt = det(d, g, n, sust) + " " + sust
        if de_alguien:
            sujeto_txt += " de " + persona()
        verbo = "estar" if random.random() < 0.6 else "ser"
        a = adj(ch(["roto", "sucio", "limpio", "mojado", "nuevo", "lindo", "grande", "chico",
                    "pesado", "lleno", "vacío", "rojo", "azul"]), g, n)
        per = "3p" if n == "p" else "3s"
        return unir(sujeto_txt, conjugar(verbo, ch(["pres", "pres", "imp"]), per), ch(["", "muy ", ""]) + a)
    if r < 0.65:
        palabra, g, tipo = ch(COMIDAS + BEBIDAS)
        n = "p" if tipo == "pl" else "s"
        sujeto_txt = det(ch(["def", "def", "este"]), g, n, palabra) + " " + palabra
        a = adj(ch(["rico", "caliente", "frío", "salado", "dulce", "feo", "riquísimo"]), g, n)
        return unir(sujeto_txt, conjugar("estar", "pres", "3p" if n == "p" else "3s"), ch(["", "muy ", ""]) + a)
    s = _ajustar_genero_pronombre(sujeto(hablante, 0.3))
    texto, per, g, n = s
    a = adj(ch(ADJ_SER), g, n)
    return unir(texto, conjugar("ser", "pres", per), ch(["", "muy ", "re "]) + a)


def cl_sensacion(hablante):
    s = sujeto(hablante, 0.75)
    texto, per = s[0], s[1]
    item = ch(SENSACIONES)
    palabra, g = item[0], item[1]
    n = item[2] if len(item) > 2 else "s"
    neg = "no " if random.random() < 0.12 else ""
    r = random.random()
    if r < 0.4 and not neg:
        cuant = det("mucho", g, n, palabra) + " "
    elif r < 0.5:
        cuant = det("poco", g, n, palabra) + " " if n == "s" else ""
    else:
        cuant = ""
    if random.random() < 0.15:
        palabra = "ganas de " + actividad_inf(per)
        cuant = ch(["", "muchas "])
    if random.random() < 0.1:
        palabra = "dolor de " + ch(["cabeza", "panza", "garganta", "oído", "muela", "estómago", "espalda"])
        cuant = ch(["", "mucho "])
    return con_tiempo(unir(texto, neg + conjugar("tener", ch(["pres", "pres", "pres", "imp"]), per), cuant + palabra),
                      ["hoy", "ahora", "desde ayer", "a la noche"], 0.2)


def cl_dolor(hablante):
    per = ch(["1s"] * 6 + ["3s", "3s", "1p", "3p", "2v"])
    parte, g = ch(CUERPO)
    n = "p" if parte in CUERPO_PL_OK and random.random() < 0.3 else "s"
    sust = parte if n == "s" else pluralizar(parte)
    pre = ""
    if per == "3s":
        pre = prep("a", persona(False))
    elif per == "3p":
        pre = prep("a", persona(True))
    elif per == "2v" and random.random() < 0.5:
        pre = "a vos"
    verbo = ch(["doler", "doler", "doler", "picar"])
    forma = conjugar(verbo, ch(["pres", "pres", "pres", "pret"]), "3p" if n == "p" else "3s")
    intens = ch(["", "", "mucho ", "un poco "])
    neg = "no " if random.random() < 0.08 else ""
    clausula = unir(pre, neg + DATIVO[per], forma, intens + det("def", g, n, sust), sust)
    if random.random() < 0.15:
        clausula = unir(clausula, ch(["desde ayer", "desde hoy", "otra vez", "cuando camino", "hace dos días"]))
    return clausula


def cl_ir(hablante):
    s = _ajustar_genero_pronombre(sujeto(hablante, 0.5))
    texto, per = s[0], s[1]
    t = ch(["pres", "pres", "pret", "pret", "fut", "perif"])
    destino = a_lugar()
    extra = ""
    r = random.random()
    if r < 0.3:
        extra = con_persona()
    elif r < 0.45:
        extra = "a " + actividad_inf(per)
    if t == "perif":
        verbo = conjugar("ir", "pres", per) + " a ir"
        lista = TIEMPO_FUT
    elif t == "pret":
        verbo, lista = conjugar("ir", "pret", per), TIEMPO_PAS
    elif t == "fut":
        verbo, lista = conjugar("ir", "fut", per), TIEMPO_FUT
    else:
        verbo, lista = conjugar("ir", "pres", per), TIEMPO_PRES + TIEMPO_FUT
    neg = "no " if random.random() < 0.12 else ""
    return con_tiempo(unir(texto, neg + verbo, destino, extra), lista, 0.5)


def cl_accion(hablante, tiempo_v=None):
    s = _ajustar_genero_pronombre(sujeto(hablante, 0.45))
    texto, per = s[0], s[1]
    v = ch(VERBOS_ACCION)
    if v == "ir":
        return cl_ir(hablante)
    t = tiempo_v or ch(["pres", "pret", "pret", "imp", "fut"])
    lista = {"pres": TIEMPO_PRES, "pret": TIEMPO_PAS, "imp": ["antes", "siempre", "cuando era chico"],
             "fut": TIEMPO_FUT}[t]
    comp = complemento(v)
    if "mi " in comp and per != "1s" and random.random() < 0.5:
        comp = comp.replace("mi ", POSESIVO[per] + " ", 1) if POSESIVO[per] != "nuestro" else comp
    neg = "no " if random.random() < 0.1 else ""
    return con_tiempo(unir(texto, neg + conj(v, t, per), comp), lista, 0.45)


def cl_gusto(hablante):
    per = ch(["1s"] * 5 + ["3s", "3p", "1p", "2v"])
    pre = ""
    if per == "3s":
        pre = prep("a", persona(False))
    elif per == "3p":
        pre = prep("a", persona(True))
    neg = "no " if random.random() < 0.25 else ""
    r = random.random()
    if r < 0.35:
        palabra, g, tipo = ch(COMIDAS)
        n = "p" if tipo == "pl" or (tipo == "cont" and random.random() < 0.6) else "s"
        sust = palabra if (n == "s" or tipo == "pl") else pluralizar(palabra)
        objeto_txt = det("def", g, n, sust) + " " + sust
    elif r < 0.55:
        objeto_txt = actividad_inf(per)
        n = "s"
    elif r < 0.75:
        palabra, g = ch(OBJETOS + OBJETOS_PL)
        n = "p" if (palabra, g) in OBJETOS_PL else "s"
        objeto_txt = sintagma(palabra, g, ch(["def", "este", "tu"]), n, ch(ADJ_OBJ + [None, None]),
                              plural_dado=(n == "p"))
    else:
        objeto_txt = ch(["los perros", "los gatos", "la música", "el fútbol", "los dibujitos",
                         "la escuela", "el verano", "la lluvia", "el ruido", "los días de sol",
                         "las películas de miedo", "ir a la plaza", "el chocolate"])
        n = "p" if objeto_txt.split()[0] in ("los", "las") else "s"
    verbo = ch(["gusta", "encanta", "molesta", "gusta", "da miedo"]) if n == "s" else \
        ch(["gustan", "encantan", "molestan", "gustan", "dan miedo"])
    intens = " mucho" if random.random() < 0.2 and "miedo" not in verbo else ""
    return unir(pre, neg + DATIVO[per], verbo + intens, objeto_txt)


def cl_ubicacion(hablante):
    s = _ajustar_genero_pronombre(sujeto(hablante, 0.35))
    texto, per = s[0], s[1]
    verbo = ch(["estar", "estar", "vivir", "quedarse"])
    t = ch(["pres", "pres", "pret"]) if verbo != "vivir" else "pres"
    return unir(texto, conj("quedarse" if verbo == "quedarse" else verbo, t, per) if verbo == "quedarse"
                else conjugar(verbo, t, per), en_lugar())


def cl_pedido(hablante):
    r = random.random()
    if r < 0.25:
        return unir(ch(["necesito", "quiero", "me das", "me pasás", "me traés", "me prestás"]),
                    ch([objeto(("def", "mi", "indef", "tu")), bebida(), comida()]))
    if r < 0.4:
        return unir("necesito ayuda", ch(["con la tarea", "para " + actividad_inf("1s"), "con " + objeto(("def", "mi")),
                                           "para ir al baño", ""]))
    if r < 0.6:
        s = ch(["", "mi mamá", "la maestra", "alguien", "mi papá", "vos"])
        per = "2v" if s in ("", "vos") else "3s"
        verbo = ch(["ayudar", "acompañar", "esperar", "llevar", "abrazar", "leer un cuento",
                    "explicar la tarea", "buscar", "escuchar", "llamar", "prestar atención"])
        partes = verbo.split(" ", 1)
        forma = conjugar(partes[0], "subj", per)
        resto = partes[1] if len(partes) > 1 else ""
        principal = ch(["necesito", "quiero", "me gustaría"])
        if principal == "me gustaría":
            forma = conjugar(partes[0], "subj", per)
        return unir(principal, "que", s if s != "vos" else "", "me", forma, resto)
    if r < 0.8:
        s = ch(["", "mi abuela", "mis amigos", "papá", "vos"])
        per = {"": "2v", "vos": "2v", "mis amigos": "3p"}.get(s, "3s")
        v = ch(["venir", "jugar", "quedarse", "volver", "venir a mi casa", "jugar conmigo",
                "quedarse conmigo", "volver temprano", "venir al acto", "me lea un cuento"])
        if v.startswith("me "):
            forma = "me " + conjugar("leer", "subj", per) + " un cuento"
        else:
            partes = v.split(" ", 1)
            base = partes[0]
            forma = conj(base, "subj", per) if base.endswith("se") else conjugar(base, "subj", per)
            if len(partes) > 1:
                forma += " " + partes[1]
        return unir(ch(["quiero", "me gustaría", "espero"]), "que", s if s != "vos" else "", forma)
    imperativos = [
        "prendé la luz", "apagá la luz", "cerrá la puerta", "abrí la ventana", "vení a jugar conmigo",
        "dame agua", "pasame la pelota", "ayudame con la tarea", "esperame un ratito",
        "traeme mi mochila", "prestame tu lápiz", "mirá mi dibujo", "escuchame", "dejame jugar",
        "llevame a la plaza", "poné música", "bajá el volumen", "subí el volumen",
        "dame un abrazo", "contame un cuento", "acompañame al baño", "sentate conmigo",
        "decime la verdad", "esperá un momento", "pasame el control", "abrí la puerta",
        "dame la mano", "tapame con la frazada", "llamá a mi mamá", "vení conmigo",
    ]
    return ch(imperativos)


def cl_causa(hablante):
    return ch([
        lambda: cl_sensacion(hablante), lambda: cl_estado(hablante), lambda: cl_dolor(hablante),
        lambda: ch(CLIMA), lambda: cl_accion(hablante, "pret"),
        lambda: unir("extraño", a_persona()), lambda: "mañana es mi cumpleaños",
        lambda: "no dormí bien", lambda: "no entiendo la tarea", lambda: "perdí " + objeto(("mi",)),
        lambda: _persona_estado(),
    ])()


def _persona_estado():
    """'mi abuela está enferma', 'mis primos están de viaje'."""
    plural = random.random() < 0.25
    if plural:
        palabra, g = ch(FAMILIA_PL)
        texto, n = "mis " + palabra, "p"
    else:
        palabra, g = ch(FAMILIA)
        texto, n = "mi " + palabra, "s"
    estado = ch(["enfermo", "triste", "cansado", "contento", "de viaje", "lejos", "ocupado", "resfriado"])
    if estado not in ("de viaje", "lejos"):
        estado = adj(estado, g, n)
    return unir(texto, conjugar("estar", "pres", "3p" if plural else "3s"), estado)


# ── Oraciones completas ───────────────────────────────────────────────────────

FRASES_SUELTAS = [
    "Hola, ¿cómo estás?", "Buenos días.", "Buenas tardes.", "Buenas noches.", "Gracias.",
    "Muchas gracias.", "De nada.", "Por favor.", "Perdón.", "Chau, nos vemos mañana.",
    "Hasta mañana.", "Sí, quiero.", "No, gracias.", "No quiero.", "Ya terminé.",
    "Ya está.", "No sé.", "No entiendo.", "¿Qué hora es?", "¿Qué día es hoy?",
    "¿Qué vamos a comer hoy?", "¿Cuándo vamos a la plaza?", "¿Cuándo viene mi papá?",
    "¿Quién me puede ayudar?", "¿Me ayudás?", "¿Jugamos?", "¿Vamos a la plaza?",
    "¿Puedo ir al baño?", "¿Puedo tomar agua?", "¿Me das agua, por favor?",
    "¿Dónde está mi mamá?", "¿Qué es eso?", "¿Por qué?", "¿Cómo se llama?",
    "¿Querés jugar conmigo?", "¿Me prestás tu lápiz?", "¿Falta mucho?", "¿Ya llegamos?",
    "Te quiero mucho.", "Te extraño.", "Estoy bien.", "Estoy mal.", "Me gusta.",
    "No me gusta.", "Tengo una pregunta.", "Necesito ir al baño.", "Quiero ir a casa.",
    "Basta, por favor.", "Esperá un momento.", "Ya vengo.", "Me voy a dormir.",
    "Feliz cumpleaños.", "Felicitaciones.", "Qué lindo.", "Qué rico.", "Qué feo.",
    "Estoy contento de verte.", "Me encanta esta canción.", "Hace frío.", "Hace calor.",
    "Está lloviendo.", "Tengo que hacer la tarea.", "Quiero que me escuches.",
    "No me molestes, por favor.", "Dejame tranquilo.", "Dejame tranquila.",
    "¿Me ayudás a atarme los cordones?", "¿Me podés ayudar?", "¿Me abrís la puerta?",
    "¿Cuánto falta para llegar?", "¿A qué hora salimos?", "¿Hoy hay escuela?",
    "Mañana no hay clases.", "Hoy es sábado.", "Hoy es mi cumpleaños.",
]

VOCATIVOS = ["mamá", "papá", "seño", "abuela", "abuelo", "profe", "doctora", "che"]


def oracion_compuesta(hablante):
    # cláusula principal elegida por peso, a veces unida a otra ("porque", "y",
    # "pero", "cuando") y con "por favor" o alguien a quien se llama
    tipos = [
        (cl_deseo, 24), (cl_estado, 10), (cl_ser, 7), (cl_sensacion, 9), (cl_dolor, 8),
        (cl_ir, 10), (cl_accion, 14), (cl_gusto, 7), (cl_ubicacion, 3), (cl_pedido, 8),
    ]
    f = random.choices([t for t, _ in tipos], [p for _, p in tipos])[0]
    principal = f(hablante)
    r = random.random()
    if r < 0.14:
        principal = unir(principal, "porque", cl_causa(hablante))
    elif r < 0.22:
        principal = unir(principal, ch(["y", "y", "pero"]), ch([cl_deseo, cl_accion, cl_estado, cl_sensacion])(hablante))
    elif r < 0.26:
        principal = principal + ", " + ch([cl_deseo, cl_accion, cl_sensacion])(hablante)
    elif r < 0.29:
        principal = unir("cuando", cl_accion(hablante, "pres"), ",") + " " + cl_deseo(hablante)
    es_pedido = f is cl_pedido or (f is cl_deseo and principal.split()[0] in ("quiero", "necesito", "puedo", "no"))
    if es_pedido and random.random() < 0.12 and "por favor" not in principal:
        principal = principal + ", por favor"
    if random.random() < 0.07:
        principal = ch(VOCATIVOS) + ", " + principal
    pregunta = f is cl_pedido and principal.startswith(("me das", "me pasás", "me traés", "me prestás"))
    if not pregunta and f is cl_deseo and principal.startswith(("puedo", "podés", "querés")) and random.random() < 0.6:
        pregunta = True
    return oracion(principal, pregunta=pregunta)


def preguntas_donde():
    palabra, g = ch(OBJETOS + OBJETOS_PL + [(p, g) for p, g in FAMILIA])
    n = "p" if (palabra, g) in OBJETOS_PL else "s"
    d = ch(["mi", "def", "tu", "mi"])
    verbo = "están" if n == "p" else "está"
    return oracion(unir("dónde", verbo, det(d, g, n, palabra), palabra), pregunta=True)


# ── Frases complementarias ────────────────────────────────────────────────────
# Construcciones que faltaban en las cláusulas de arriba. Se generan aparte y
# con su propia semilla para no cambiar las frases ya existentes.

CANTIDAD_COMPLEMENTARIAS = 3000
VEHICULOS = [("colectivo", "m"), ("micro", "m"), ("tren", "m"), ("auto", "m"), ("combi", "f"),
             ("subte", "m"), ("taxi", "m")]
PEDIDOS = [("comida", "f"), ("pizza", "f"), ("pedido", "m"), ("helado", "m"), ("empanadas", "f")]
EXTRAS_LLEGADA = {
    "venir": ["a casa", "a buscarme", "a jugar conmigo", "a cenar", "del trabajo", "de la escuela",
              "temprano", "tarde", "en un rato", "a visitarme", "de viaje"],
    "llegar": ["a casa", "del trabajo", "de la escuela", "temprano", "tarde", "en un rato", "de viaje"],
    "volver": ["a casa", "del trabajo", "de la escuela", "temprano", "tarde", "en un rato", "de viaje"],
    "salir": ["del trabajo", "de la escuela", "temprano", "tarde", "en un rato", "de viaje"],
    "entrar": ["a jugar conmigo", "en un rato", "a la pieza", "al aula"],
}
EVENTOS_QUE_EMPIEZAN = ["la película", "la clase", "el partido", "el acto", "la fiesta", "el recreo",
                        "el cumpleaños", "mi programa", "los dibujitos", "las vacaciones", "la terapia"]
TIEMPO_LLEGADA = {
    "pres": ["hoy", "ahora", "a la tarde", "a la noche", "después", "más tarde", "esta tarde",
             "todos los días", "siempre", "a veces", "ya"],
    "pret": TIEMPO_PAS + ["ya"],
    "fut": TIEMPO_FUT,
}
PLATOS_CON_PAPAS = ["papas fritas", "papas al horno", "puré de papas", "papas", "papas con queso",
                    "pollo con papas", "carne con papas", "bife con papas", "una hamburguesa con papas",
                    "huevo frito con papas", "salchichas con papas", "pescado con papas"]


def cl_llegada(hablante):
    """Sujeto después del verbo: 'hoy viene mi abuela', 'ya llegó el
    colectivo', '¿a qué hora vuelve mi papá?'. Sin estas frases el corrector
    aprendía que 'verbo + mi + persona' siempre lleva la 'a' personal
    ('visito a mi abuela') y corregía 'viene mi abuela' -> 'viene a mi abuela'."""
    r = random.random()
    plural = False
    habitual = True
    if r < 0.6:
        plural = random.random() < 0.2
        suj = persona(plural)
        v = ch(["venir", "venir", "llegar", "llegar", "volver", "salir", "entrar"])
        extra = ch(["", ""] + EXTRAS_LLEGADA[v] + (["con " + persona(False)] if v != "entrar" else []))
        if suj in extra:
            extra = ""
    elif r < 0.8:
        palabra, g = ch(VEHICULOS + PEDIDOS)
        plural = palabra.endswith("s")
        suj = det("def", g, "p" if plural else "s", palabra) + " " + palabra
        v = ch(["venir", "llegar", "llegar"] + (["pasar", "salir"] if (palabra, g) in VEHICULOS else []))
        extra = ch(["", "", "", "tarde", "temprano", "en un rato"])
    else:
        suj = ch(EVENTOS_QUE_EMPIEZAN)
        plural = suj.split()[0] in ("los", "las")
        v = ch(["empezar", "empezar", "terminar"])
        extra = ""
        habitual = False
    per = "3p" if plural else "3s"
    t = ch(["pres", "pres", "pret", "pret", "fut", "perif"])
    if t == "perif":
        forma, lista = conjugar("ir", "pres", per) + " a " + v, TIEMPO_FUT
    else:
        forma, lista = conjugar(v, t, per), TIEMPO_LLEGADA[t]
    if not habitual:
        lista = [x for x in lista if x not in ("todos los días", "siempre", "a veces")]
    temporal = extra in ("temprano", "tarde", "en un rato")
    if temporal and t == "pret" and extra == "en un rato":
        extra, temporal = "", False
    if random.random() < 0.15:
        return oracion(unir(ch(["cuándo", "a qué hora"]), forma, suj, "" if temporal else extra), pregunta=True)
    neg = "no " if random.random() < 0.1 else ""
    clausula = unir(neg + forma, suj, extra)
    return oracion(clausula if temporal else con_tiempo(clausula, lista, 0.7))


def cl_papas(hablante):
    """'Papas' la comida, para que el corrector no las confunda con 'papás'."""
    r = random.random()
    if r < 0.6:
        principal = ch(["quiero comer", "quiero", "me gustaría comer", "hoy comí", "ayer comimos",
                        "vamos a comer", "de cena hay", "hoy hay", "mi mamá hizo", "mi abuela hizo",
                        "mi papá está cocinando", "necesito", "me das", "en el comedor hay",
                        "mi tía va a hacer", "para el almuerzo quiero"])
        texto = unir(principal, ch(PLATOS_CON_PAPAS))
        return oracion(texto, pregunta=principal in ("me das",))
    if r < 0.85:
        neg = "no " if random.random() < 0.25 else ""
        verbo = ch(["gustan", "encantan", "gustan"])
        quien = ch(["", "", "a mi hermano", "a mi papá", "a mis primos", "a vos"])
        dat = {"": "me", "a vos": "te"}.get(quien, "le" if quien != "a mis primos" else "les")
        return oracion(unir(quien, neg + dat, verbo, "las", ch(["papas", "papas fritas", "papas al horno"])))
    return oracion(unir(ch(["ayudo a mi abuela a", "voy a ayudar a", "mi mamá me enseñó a", "tengo que"]),
                        ch(["pelar las papas", "lavar las papas", "cortar las papas"])))


def complementarias(semilla):
    random.seed(semilla)
    frases = set()
    intentos = 0
    while len(frases) < CANTIDAD_COMPLEMENTARIAS and intentos < CANTIDAD_COMPLEMENTARIAS * 5:
        intentos += 1
        f = cl_llegada if random.random() < 0.8 else cl_papas
        frases.add(f(ch("mf")))
    return frases


def generar(cantidad, semilla=42):
    # frases sueltas + compuestas sin repetir, con semilla fija (el corpus no
    # cambia entre corridas)
    random.seed(semilla)
    frases = set(FRASES_SUELTAS)
    intentos = 0
    while len(frases) < cantidad and intentos < cantidad * 5:
        intentos += 1
        hablante = ch("mf")
        if random.random() < 0.04:
            frases.add(preguntas_donde())
        else:
            frases.add(oracion_compuesta(hablante))
    frases |= complementarias(semilla + 1)
    return sorted(frases)


def main():
    frases = generar(CANTIDAD)
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        for frase in frases:
            f.write(frase + "\n")
    print(f"{len(frases)} frases -> {SALIDA}")
    random.seed(7)
    for frase in random.sample(frases, 40):
        print("  ", frase)


# Uso (desde IA/): python scripts/datos/corpus_caa.py
if __name__ == "__main__":
    main()
