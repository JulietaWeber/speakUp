"""
Generador de conceptos LARGOS (6-10 palabras de entrada) para el dataset de
corrección: bolsa de palabras sueltas -> frase natural en español.

Los conceptos curados a mano (conceptos_correccion.jsonl) casi no tienen
frases largas, y por eso el modelo armaba mal las de 7+ palabras. Escribir
miles a mano no escala, así que acá se componen a partir de bancos chicos y
semánticamente coherentes (lugares con sus actividades, acciones con sus
objetos posibles, motivos, eventos...) y plantillas de oración típicas de CAA.

Toda la concordancia se resuelve acá de forma explícita, porque es justo lo
que el modelo tiene que aprender:
- el usuario elige la forma base ("frío", "enfermo", "mucho") y la frase usa
  la forma concordada ("tengo mucha hambre", "mi abuela está enferma",
  "una flor roja");
- artículos y contracciones según género/número ("al parque", "el agua",
  "las zapatillas");
- verbos conjugados según persona y tiempo ("me duelen las piernas", "ayer
  fui al cine y vi una película", "mi papá me ayude").

Cada concepto cumple la misma regla que los curados (solo palabras de la
entrada, sus flexiones y glue gramatical); dataset_correccion.py lo vuelve a
validar antes de escribir el dataset.
"""

import random

from conjugacion import conjugar_yo
from gramatica import flexionar

# ── Personas ─────────────────────────────────────────────────────────────────

PERSONAS = {   # palabra -> género
    "mamá": "f", "papá": "m", "hermano": "m", "hermana": "f", "abuela": "f",
    "abuelo": "m", "amigo": "m", "amiga": "f", "primo": "m", "prima": "f",
    "tío": "m", "tía": "f",
}
PERSONAS_CON_ARTICULO = {"maestra": "f", "seño": "f", "profesor": "m"}
MASCOTAS = {"perro": "m", "gato": "m", "perra": "f"}
# con quién se puede hacer algo ("con mi familia", "con mi vecino"): además
# de PERSONAS, grupos y personas que no encajan en todos los eventos
# ("es el cumpleaños de mi familia" no tiene sentido)
ACOMPAÑANTES = list(PERSONAS) + ["familia", "vecino", "vecina", "padrino", "madrina"]


def persona(p):
    """'mi mamá', 'la maestra', 'mi perro'."""
    if p in PERSONAS_CON_ARTICULO:
        return ("la " if PERSONAS_CON_ARTICULO[p] == "f" else "el ") + p
    return "mi " + p


def a_persona(p):
    t = persona(p)
    return "al " + t[3:] if t.startswith("el ") else "a " + t


def genero_persona(p):
    return {**PERSONAS, **PERSONAS_CON_ARTICULO, **MASCOTAS,
            "familia": "f", "vecino": "m", "vecina": "f", "padrino": "m", "madrina": "f"}[p]


# ── Concordancia ─────────────────────────────────────────────────────────────

def articulo(sust, genero, numero, tipo):
    if tipo == "none":
        return ""
    if tipo == "mi":
        return "mis" if numero == "p" else "mi"
    if tipo == "def":
        if numero == "p":
            return "las" if genero == "f" else "los"
        if genero == "f" and sust in ("agua", "águila", "hacha", "arma"):
            return "el"
        return "la" if genero == "f" else "el"
    if numero == "p":
        return "unas" if genero == "f" else "unos"
    return "una" if genero == "f" else "un"


def con_articulo(sust, genero, numero, tipo):
    art = articulo(sust, genero, numero, tipo)
    return f"{art} {sust}" if art else sust


# ── Lugares y lo que se hace en cada uno ─────────────────────────────────────

LUGARES = {   # palabra -> artículo (None = sin artículo: "a casa", "en casa")
    "parque": "el", "plaza": "la", "escuela": "la", "casa": None, "playa": "la",
    "cine": "el", "club": "el", "pileta": "la", "cancha": "la", "kiosco": "el",
    "supermercado": "el", "biblioteca": "la", "heladería": "la",
    "zoológico": "el", "campo": "el", "shopping": "el",
}

# lugar -> [(verbo, palabras extra de la bolsa, texto del complemento)]
ACTIVIDADES_LUGAR = {
    "parque": [("jugar", ["pelota"], "a la pelota"), ("andar", ["bicicleta"], "en bicicleta"),
               ("correr", [], ""), ("jugar", ["hamacas"], "en las hamacas")],
    "plaza": [("jugar", ["tobogán"], "en el tobogán"), ("andar", ["patineta"], "en patineta"),
              ("jugar", ["arena"], "con la arena")],
    "playa": [("nadar", ["mar"], "en el mar"), ("jugar", ["arena"], "en la arena"),
              ("buscar", ["caracoles"], "caracoles")],
    "pileta": [("nadar", [], ""), ("jugar", ["agua"], "en el agua")],
    "cine": [("ver", ["película"], "una película"), ("comer", ["pochoclos"], "pochoclos")],
    "club": [("jugar", ["fútbol"], "al fútbol"), ("nadar", [], ""), ("jugar", ["básquet"], "al básquet")],
    "cancha": [("jugar", ["fútbol"], "al fútbol"), ("ver", ["partido"], "el partido")],
    "kiosco": [("comprar", ["caramelos"], "caramelos"), ("comprar", ["chicle"], "un chicle"),
               ("comprar", ["alfajor"], "un alfajor")],
    "supermercado": [("comprar", ["leche"], "leche"), ("comprar", ["fruta"], "fruta"),
                     ("comprar", ["galletitas"], "galletitas")],
    "biblioteca": [("buscar", ["libro"], "un libro"), ("leer", ["cuentos"], "cuentos")],
    "heladería": [("comprar", ["helado"], "un helado"), ("tomar", ["helado"], "un helado")],
    "zoológico": [("ver", ["leones"], "los leones"), ("ver", ["animales"], "los animales"),
                  ("ver", ["jirafas"], "las jirafas")],
    "escuela": [("ver", ["amigos"], "a mis amigos"), ("jugar", ["recreo"], "en el recreo")],
    "campo": [("andar", ["caballo"], "a caballo"), ("ver", ["vacas"], "las vacas")],
    "casa": [("jugar", ["videojuegos"], "a los videojuegos"), ("ver", ["tele"], "la tele"),
             ("descansar", [], "")],
    "shopping": [("comprar", ["ropa"], "ropa"), ("ver", ["vidrieras"], "las vidrieras")],
}


def a_lugar(l):
    art = LUGARES[l]
    if art is None:
        return f"a {l}"
    return f"al {l}" if art == "el" else f"a la {l}"


def en_lugar(l):
    art = LUGARES[l]
    return f"en {l}" if art is None else f"en {art} {l}"


# ── Acciones con objeto (en casa o en general) ───────────────────────────────

# verbo -> [(sustantivo, género, número, tipo de artículo)]
OBJETOS = {
    "comer": [("pizza", "f", "s", "none"), ("milanesa", "f", "s", "indef"), ("fideos", "m", "p", "none"),
              ("torta", "f", "s", "none"), ("galletitas", "f", "p", "none"), ("manzana", "f", "s", "indef"),
              ("sándwich", "m", "s", "indef"), ("empanadas", "f", "p", "none"), ("sopa", "f", "s", "none"),
              ("banana", "f", "s", "indef"), ("helado", "m", "s", "none"), ("arroz", "m", "s", "none")],
    "tomar": [("agua", "f", "s", "none"), ("leche", "f", "s", "none"), ("jugo", "m", "s", "none"),
              ("chocolatada", "f", "s", "none"), ("té", "m", "s", "none"), ("remedio", "m", "s", "def")],
    "ver": [("película", "f", "s", "indef"), ("tele", "f", "s", "def"), ("dibujitos", "m", "p", "none"),
            ("partido", "m", "s", "def"), ("fotos", "f", "p", "def"), ("video", "m", "s", "indef")],
    "leer": [("libro", "m", "s", "indef"), ("cuento", "m", "s", "indef"), ("revista", "f", "s", "indef"),
             ("historieta", "f", "s", "indef")],
    "dibujar": [("flor", "f", "s", "indef"), ("casa", "f", "s", "indef"), ("perro", "m", "s", "indef"),
                ("árbol", "m", "s", "indef"), ("mariposa", "f", "s", "indef"), ("auto", "m", "s", "indef")],
    "pintar": [("dibujo", "m", "s", "def"), ("cuadro", "m", "s", "indef"), ("caja", "f", "s", "def")],
    "escuchar": [("música", "f", "s", "none"), ("canción", "f", "s", "indef"), ("cuento", "m", "s", "indef")],
    "armar": [("rompecabezas", "m", "s", "indef"), ("torre", "f", "s", "indef"), ("castillo", "m", "s", "indef")],
    "comprar": [("zapatillas", "f", "p", "none"), ("remera", "f", "s", "indef"), ("pelota", "f", "s", "indef"),
                ("juguete", "m", "s", "indef"), ("helado", "m", "s", "indef"), ("mochila", "f", "s", "indef")],
    "usar": [("computadora", "f", "s", "def"), ("tablet", "f", "s", "def"), ("tijera", "f", "s", "def")],
    "buscar": [("mochila", "f", "s", "def"), ("campera", "f", "s", "def"), ("zapatillas", "f", "p", "def"),
               ("anteojos", "m", "p", "def"), ("pelota", "f", "s", "def")],
    "cocinar": [("torta", "f", "s", "indef"), ("galletitas", "f", "p", "none"), ("fideos", "m", "p", "none")],
    "escribir": [("carta", "f", "s", "indef"), ("cuento", "m", "s", "indef"), ("nombre", "m", "s", "mi"),
                 ("mensaje", "m", "s", "indef")],
    "cenar": [("milanesas", "f", "p", "none"), ("pizza", "f", "s", "none"), ("fideos", "m", "p", "none"),
              ("sopa", "f", "s", "none")],
    "almorzar": [("milanesas", "f", "p", "none"), ("arroz", "m", "s", "none"), ("pollo", "m", "s", "none")],
    "desayunar": [("leche", "f", "s", "none"), ("tostadas", "f", "p", "none"), ("cereales", "m", "p", "none")],
    "merendar": [("galletitas", "f", "p", "none"), ("tostadas", "f", "p", "none"), ("chocolatada", "f", "s", "none")],
}

# Dónde se hace cada acción dentro de la casa ("en la cama", "en el sillón").
LUGARES_CASA = {"cama": "la", "sillón": "el", "cocina": "la", "patio": "el", "pieza": "la",
                "mesa": "la", "living": "el", "comedor": "el"}
DONDE_ACCION = {
    "comer": ["mesa", "cocina", "comedor"], "tomar": ["cocina", "mesa"], "cocinar": ["cocina"],
    "leer": ["cama", "sillón", "patio"], "ver": ["sillón", "living", "pieza"],
    "dibujar": ["mesa", "patio"], "pintar": ["mesa", "patio"], "escribir": ["mesa", "pieza"],
    "armar": ["pieza", "living", "mesa"], "escuchar": ["pieza", "cama"], "usar": ["pieza", "mesa"],
    "buscar": ["pieza", "patio", "cocina"], "cenar": ["comedor", "cocina"], "almorzar": ["comedor", "cocina"],
    "desayunar": ["cocina", "cama"], "merendar": ["patio", "cocina"],
}
# Con qué se dibuja / pinta / escribe, y sobre qué.
INSTRUMENTOS = [("lápiz", "m", "s"), ("lápices", "m", "p"), ("crayones", "m", "p"),
                ("fibras", "f", "p"), ("pincel", "m", "s"), ("témperas", "f", "p")]
SOPORTES = [("cuaderno", "m"), ("hoja", "f"), ("pizarrón", "m")]
COLORES = ["rojo", "azul", "verde", "amarillo", "negro"]

ADJETIVOS = {
    "comer": ["rico", "caliente"],
    "tomar": ["frío", "caliente"],
    "dibujar": ["rojo", "azul", "verde", "amarillo", "grande", "lindo"],
    "pintar": ["rojo", "azul", "verde", "amarillo"],
    "comprar": ["rojo", "azul", "nuevo", "lindo", "grande"],
    "leer": ["nuevo", "largo"],
    "armar": ["grande", "nuevo"],
    "buscar": ["nuevo", "azul", "rojo"],
    "cocinar": ["rico", "grande"],
}
SABORES = {"helado", "torta", "galletitas", "alfajor"}
GUSTOS = ["chocolate", "frutilla", "vainilla", "limón"]
NO_ADJ = {"remedio", "tele", "partido", "fotos", "dibujitos", "música", "rompecabezas"}


def objeto(verbo, rng):
    """(palabras de la bolsa, texto) del objeto de `verbo`, a veces con un
    adjetivo concordado o un sabor, y en dibujar/pintar/escribir a veces con
    el instrumento ("con los crayones rojos") y el soporte ("en el cuaderno")."""
    sust, gen, num, tipo = rng.choice(OBJETOS[verbo])
    bolsa = [sust]
    texto = con_articulo(sust, gen, num, tipo)
    r = rng.random()
    con_adj = False
    if sust in SABORES and r < 0.35:
        gusto = rng.choice(GUSTOS)
        bolsa.append(gusto)
        texto += f" de {gusto}"
    elif verbo in ADJETIVOS and sust not in NO_ADJ and r < 0.6:
        adj = rng.choice(ADJETIVOS[verbo])
        bolsa.append(adj)
        texto += " " + flexionar(adj, gen, num)
        con_adj = True
    if verbo in ("dibujar", "pintar", "escribir"):
        if rng.random() < 0.5:
            ins, g, n = rng.choice(INSTRUMENTOS)
            bolsa.append(ins)
            texto += f" con {con_articulo(ins, g, n, 'def')}"
            if not con_adj and rng.random() < 0.4:
                color = rng.choice([c for c in COLORES if c not in bolsa])
                bolsa.append(color)
                texto += " " + flexionar(color, g, n)
        if verbo != "pintar" and rng.random() < 0.35:
            sop, g = rng.choice(SOPORTES)
            bolsa.append(sop)
            texto += f" en {con_articulo(sop, g, 's', 'def')}"
    return bolsa, texto


def en_casa(verbo, rng):
    """(bolsa, texto) opcional de dónde se hace `verbo` dentro de la casa."""
    if verbo in DONDE_ACCION and rng.random() < 0.35:
        lugar = rng.choice(DONDE_ACCION[verbo])
        return [lugar], f"en {LUGARES_CASA[lugar]} {lugar}"
    return [], ""


# ── Motivos ("porque ...") y contrastes ("pero ...") ─────────────────────────

SENSACIONES = {"hambre": "f", "sed": "f", "frío": "m", "calor": "m", "sueño": "m", "miedo": "m"}
ESTADOS = ["cansado", "aburrido", "triste", "enfermo", "nervioso", "contento", "enojado",
           "preocupado", "feliz", "emocionado"]
DOLORES = {"panza": ("f", "s"), "cabeza": ("f", "s"), "garganta": ("f", "s"), "muela": ("f", "s"),
           "piernas": ("f", "p"), "pies": ("m", "p"), "oídos": ("m", "p"), "brazo": ("m", "s"),
           "espalda": ("f", "s")}


MOTIVOS_NEGATIVOS = ["estado", "estado", "dolor", "dolor", "clima", "noche", "tarea",
                     "persona_estado", "objeto_estado", "miedo"]
MIEDOS = [("oscuridad", "f", "s"), ("tormenta", "f", "s"), ("truenos", "m", "p"),
          ("perros", "m", "p"), ("monstruos", "m", "p"), ("ruido", "m", "s")]


def _prep_a(sintagma):
    """'a' + sintagma, con contracción: 'el ruido' -> 'al ruido'."""
    return "al " + sintagma[3:] if sintagma.startswith("el ") else "a " + sintagma
MOTIVOS_POSITIVOS = ["aburrido", "persona_viene", "cumple", "extrañar"]
# motivos específicos según lo que se quiere hacer
SENSACION_PARA = {"comer": ["hambre"], "cocinar": ["hambre"], "tomar": ["sed", "calor", "frío"],
                  "pileta": ["calor"], "playa": ["calor"], "heladería": ["calor"],
                  "casa": ["frío", "sueño"], "dormir": ["sueño"]}


def motivo(rng, personas_usadas, negativo=False, pista=None):
    """(bolsa, texto) de una cláusula de motivo coherente con la oración:
    `negativo` para "no quiero / no puedo ... porque" (cansancio, dolor,
    clima...), si no, motivos para querer hacer algo; `pista` (verbo o lugar)
    habilita motivos específicos ("quiero comer ... porque tengo hambre")."""
    if negativo:
        tipo = rng.choice(MOTIVOS_NEGATIVOS)
    elif pista in SENSACION_PARA and rng.random() < 0.6:
        tipo = "sensacion"
    else:
        tipo = rng.choice(MOTIVOS_POSITIVOS)
    if tipo == "sensacion":
        s = rng.choice(SENSACION_PARA[pista])
        if rng.random() < 0.4:
            return ["tener", s, "mucho"], f"tengo {flexionar('mucho', SENSACIONES[s])} {s}"
        return ["tener", s], f"tengo {s}"
    if tipo == "aburrido":
        if rng.random() < 0.35:
            return ["estar", "muy", "aburrido"], "estoy muy aburrido"
        return ["estar", "aburrido"], "estoy aburrido"
    if tipo == "estado":
        e = rng.choice(["cansado", "enfermo", "triste", "nervioso"])
        if rng.random() < 0.35:
            return ["estar", "muy", e], f"estoy muy {e}"
        return ["estar", e], f"estoy {e}"
    if tipo == "dolor":
        d = rng.choice(list(DOLORES))
        gen, num = DOLORES[d]
        verbo = "duelen" if num == "p" else "duele"
        art = articulo(d, gen, num, "def")
        if rng.random() < 0.35:
            return ["doler", d, "mucho"], f"me {verbo} mucho {art} {d}"
        return ["doler", d], f"me {verbo} {art} {d}"
    if tipo == "clima":
        c = rng.choice(["calor", "frío", "llover"])
        if c == "llover":
            return lluvia(rng)
        if rng.random() < 0.4:
            return ["hacer", c, "mucho"], f"hace mucho {c}"
        return ["hacer", c], f"hace {c}"
    if tipo == "noche":
        if rng.random() < 0.5:
            return ["no", "dormir", "anoche"], "anoche no dormí"
        return ["no", "dormir", "bien", "anoche"], "anoche no dormí bien"
    if tipo == "tarea":
        return ["no", "terminar", "tarea"], "no terminé la tarea"
    if tipo == "miedo":
        sust, gen, num = rng.choice(MIEDOS)
        return ["tener", "miedo", sust], f"tengo miedo {_prep_a(con_articulo(sust, gen, num, 'def'))}"
    if tipo == "objeto_estado":
        sust, gen, num, adj = rng.choice([("mochila", "f", "s", "pesado"), ("ropa", "f", "s", "sucio"),
                                          ("zapatillas", "f", "p", "mojado"), ("pantalón", "m", "s", "roto"),
                                          ("piso", "m", "s", "mojado"), ("juguetes", "m", "p", "roto")])
        verbo = "están" if num == "p" else "está"
        return [sust, "estar", adj], f"{con_articulo(sust, gen, num, 'def')} {verbo} {flexionar(adj, gen, num)}"
    p = rng.choice([q for q in PERSONAS if q not in personas_usadas])
    personas_usadas.add(p)
    if tipo == "persona_estado":
        e = rng.choice(["enfermo", "cansado", "triste", "enojado"])
        return [p, "estar", e], f"{persona(p)} está {flexionar(e, genero_persona(p))}"
    if tipo == "persona_viene":
        return [p, "venir", "casa"], f"{persona(p)} viene a casa"
    if tipo == "cumple":
        return ["ser", "cumpleaños", p], f"es el cumpleaños de {persona(p)}"
    # extrañar
    return ["extrañar", p], f"extraño {a_persona(p)}"


def lluvia(rng):
    if rng.random() < 0.5:
        return ["estar", "llover"], "está lloviendo"
    return ["llover"], "llueve"


AL_AIRE_LIBRE = {"parque", "plaza", "playa", "pileta", "club", "cancha", "zoológico", "campo"}


# ── Tiempo ───────────────────────────────────────────────────────────────────

TIEMPO_ADELANTE = ["hoy", "mañana", "ahora", "después"]
TIEMPO_ATRAS = {"noche": "esta noche", "tarde": "esta tarde", "sábado": "el sábado",
                "domingo": "el domingo"}


def tiempo(rng):
    """(bolsa, texto, va_adelante) o None."""
    r = rng.random()
    if r < 0.3:
        t = rng.choice(TIEMPO_ADELANTE)
        return [t], t, True
    if r < 0.5:
        t = rng.choice(list(TIEMPO_ATRAS))
        return [t], TIEMPO_ATRAS[t], False
    if r < 0.55:
        return ["fin", "semana"], "el fin de semana", False
    return None


# ── Plantillas ───────────────────────────────────────────────────────────────

MODALES = {"querer": "quiero", "necesitar": "necesito", "poder": "puedo", "ganas": "tengo ganas de"}


def _modal(rng, negar):
    opciones = ["querer", "querer", "poder", "poder", "ganas"] if negar else ["querer", "querer", "querer", "necesitar", "ganas"]
    m = rng.choice(opciones)
    bolsa = ["tener", "ganas"] if m == "ganas" else [m]
    texto = ("no " if negar else "") + MODALES[m]
    return (["no"] if negar else []) + bolsa, texto


def plantilla_ir(rng):
    """[tiempo] [no] quiero ir al parque [con mi hermano] [a jugar a la pelota]
    [esta tarde] [porque ...]"""
    negar = rng.random() < 0.3
    bolsa, texto = _modal(rng, negar)
    lugar = rng.choice(list(LUGARES))
    bolsa += ["ir", lugar]
    texto += f" ir {a_lugar(lugar)}"
    usadas = set()
    if rng.random() < 0.55:
        p = rng.choice(ACOMPAÑANTES + list(PERSONAS_CON_ARTICULO))
        usadas.add(p)
        bolsa.append(p)
        texto += f" con {persona(p)}"
    if not negar and rng.random() < 0.7:
        verbo, extra, comp = rng.choice(ACTIVIDADES_LUGAR[lugar])
        bolsa += [verbo] + extra
        texto += f" a {verbo}" + (f" {comp}" if comp else "")
    t = tiempo(rng)
    adelante = atras = ""
    if t:
        bolsa += t[0]
        if t[2]:
            adelante = t[1]
        else:
            atras = t[1]
    cuerpo = " ".join(x for x in [adelante, texto, atras] if x)
    r = rng.random()
    if negar or r < 0.4:
        mb, mt = motivo(rng, usadas, negativo=negar, pista=lugar)
        return bolsa + ["porque"] + mb, f"{cuerpo} porque {mt}"
    if r < 0.55 and lugar in AL_AIRE_LIBRE:
        cb, ct = lluvia(rng) if rng.random() < 0.6 else (["hacer", "frío"], "hace frío")
        return bolsa + ["pero"] + cb, f"{cuerpo} pero {ct}"
    return bolsa, cuerpo


def plantilla_accion(rng):
    """[tiempo] [no] quiero comer una milanesa rica [con mi abuela] [esta noche]
    [porque ... | pero ...]"""
    negar = rng.random() < 0.25
    bolsa, texto = _modal(rng, negar)
    verbo = rng.choice(list(OBJETOS))
    ob, ot = objeto(verbo, rng)
    bolsa += [verbo] + ob
    texto += f" {verbo} {ot}"
    usadas = set()
    if rng.random() < 0.4:
        p = rng.choice(ACOMPAÑANTES)
        usadas.add(p)
        bolsa.append(p)
        texto += f" con {persona(p)}"
    lb, lt = en_casa(verbo, rng)
    if lb and lb[0] not in bolsa:
        bolsa += lb
        texto += f" {lt}"
    t = tiempo(rng)
    adelante = atras = ""
    if t:
        bolsa += t[0]
        adelante, atras = (t[1], "") if t[2] else ("", t[1])
    cuerpo = " ".join(x for x in [adelante, texto, atras] if x)
    r = rng.random()
    if negar or r < 0.35:
        mb, mt = motivo(rng, usadas, negativo=negar, pista=verbo)
        return bolsa + ["porque"] + mb, f"{cuerpo} porque {mt}"
    if r < 0.6 and not negar:
        contras = [
            (["estar", "cansado"], "estoy cansado"), (["no", "poder"], "no puedo"),
            (["no", "tener", "tiempo"], "no tengo tiempo"),
        ] + [([p, "no", "querer"], f"{persona(p)} no quiere") for p in ("mamá", "papá", "abuela") if p not in usadas] \
          + [([p, "no", "dejar"], f"{persona(p)} no me deja") for p in ("mamá", "papá") if p not in usadas]
        if verbo == "comprar":
            contras += [(["no", "tener", "plata"], "no tengo plata")] * 3
        cb, ct = rng.choice(contras)
        return bolsa + ["pero"] + cb, f"{cuerpo} pero {ct}"
    return bolsa, cuerpo


def _accion_simple(rng, pasado=False):
    """(bolsa, texto) de 'comer una pizza' / 'comí una pizza'."""
    verbo = rng.choice(list(OBJETOS))
    ob, ot = objeto(verbo, rng)
    forma = conjugar_yo(verbo, pasado=True) if pasado else verbo
    return [verbo] + ob, f"{forma} {ot}"


def plantilla_pasado(rng):
    """Ayer fui al cine con mi tía y vi una película."""
    lugar = rng.choice([l for l in LUGARES if l != "casa"])
    p = rng.choice(ACOMPAÑANTES)
    bolsa = ["ayer", "ir", lugar]
    texto = f"ayer fui {a_lugar(lugar)}"
    if rng.random() < 0.75:
        bolsa.append(p)
        texto += f" con {persona(p)}"
    verbo, extra, comp = rng.choice(ACTIVIDADES_LUGAR[lugar])
    if rng.random() < 0.5:
        bolsa.append("y")
    bolsa += [verbo] + extra
    texto += f" y {conjugar_yo(verbo, pasado=True)}" + (f" {comp}" if comp else "")
    if rng.random() < 0.3:
        e = rng.choice(["contento", "cansado", "feliz"])
        bolsa += ["estar", e]
        # "Ayer fui al parque y jugué a la pelota, ahora estoy cansado."
        texto += f", ahora estoy {e}"
        bolsa.append("ahora")
    return bolsa, texto


def plantilla_dos_acciones(rng):
    """Quiero tomar leche y comer galletitas antes de dormir."""
    bolsa, texto = _modal(rng, False)
    b1, t1 = _accion_simple(rng)
    b2, t2 = _accion_simple(rng)
    if b1[0] == b2[0] or set(b1) & set(b2):
        return None
    bolsa += b1 + (["y"] if rng.random() < 0.5 else []) + b2
    texto += f" {t1} y {t2}"
    comidas = {"cenar", "almorzar", "desayunar", "merendar"}
    if rng.random() < 0.5 and not comidas & {b1[0], b2[0]}:
        cb, ct = rng.choice(MOMENTOS_DEL_DIA)
        bolsa += cb
        texto += f" {ct}"
    return bolsa, texto


MOMENTOS_DEL_DIA = [
    (["antes", "dormir"], "antes de dormir"), (["después", "escuela"], "después de la escuela"),
    (["después", "cenar"], "después de cenar"), (["antes", "comer"], "antes de comer"),
    (["después", "almorzar"], "después de almorzar"), (["antes", "bañarme"], "antes de bañarme"),
]


EVENTOS_FELICES = [
    lambda p: ([p, "venir", "casa"], f"{persona(p)} viene a casa"),
    lambda p: ([p, "regalar", "juguete"], f"{persona(p)} me regaló un juguete"),
    lambda p: ([p, "regalar", "pelota"], f"{persona(p)} me regaló una pelota"),
    lambda p: (["ser", "cumpleaños", p], f"es el cumpleaños de {persona(p)}"),
    lambda p: ([p, "llevar", "parque"], f"{persona(p)} me lleva al parque"),
    lambda p: (["ir", "jugar", p], f"voy a jugar con {persona(p)}"),
]
_ENFERMO = lambda p: ([p, "estar", "enfermo"], f"{persona(p)} está {flexionar('enfermo', genero_persona(p))}")
EVENTOS_NEGATIVOS = {
    "triste": [_ENFERMO, lambda p: ([p, "no", "venir"], f"{persona(p)} no vino"),
               lambda p: (["extrañar", p], f"extraño {a_persona(p)}")],
    "enojado": [lambda p: ([p, "no", "querer", "jugar"], f"{persona(p)} no quiere jugar conmigo"),
                lambda p: ([p, "romper", "juguete"], f"{persona(p)} rompió mi juguete")],
    "preocupado": [_ENFERMO],
    "nervioso": [lambda p: (["tener", "prueba", "mañana"], "mañana tengo una prueba"),
                 lambda p: (["ir", "dentista", "mañana"], "mañana voy al dentista"),
                 lambda p: (["ir", "médico", "hoy"], "hoy voy al médico")],
}


def plantilla_sentimiento(rng):
    """Hoy estoy muy contento porque mi abuela viene a casa."""
    feliz = rng.random() < 0.55
    e = rng.choice(["contento", "feliz", "emocionado"] if feliz else list(EVENTOS_NEGATIVOS))
    bolsa = ["estar", e]
    texto = f"estoy {e}"
    if rng.random() < 0.4:
        bolsa.insert(1, "muy")
        texto = f"estoy muy {e}"
    t = rng.choice([None, None, "hoy", "ahora"])
    if t:
        bolsa.append(t)
        texto = f"{t} {texto}"
    p = rng.choice(list(PERSONAS) + list(MASCOTAS) if not feliz else list(PERSONAS))
    eb, et = rng.choice(EVENTOS_FELICES if feliz else EVENTOS_NEGATIVOS[e])(p)
    if t and t in eb:
        return None
    bolsa += ["porque"] + eb
    texto += f" porque {et}"
    if feliz and "mañana" not in bolsa and rng.random() < 0.3 and "venir" in eb:
        bolsa.append("mañana")
        texto += " mañana"
    return bolsa, texto


def plantilla_tercera_persona(rng):
    """Mi hermana está cansada y quiere dormir. / Mi perro tiene hambre y quiere comer."""
    p = rng.choice(list(PERSONAS) + list(MASCOTAS))
    g = genero_persona(p)
    r = rng.random()
    if r < 0.5:
        s = rng.choice(["hambre", "sed", "sueño", "frío", "calor"])
        bolsa, texto = [p, "tener", s], f"{persona(p)} tiene {s}"
    else:
        e = rng.choice(["cansado", "aburrido", "enfermo", "triste", "contento"])
        bolsa, texto = [p, "estar", e], f"{persona(p)} está {flexionar(e, g)}"
    if rng.random() < 0.5:
        bolsa.append("y")
    if p in MASCOTAS:
        v, ob, ot = rng.choice([("comer", [], ""), ("tomar", ["agua"], " agua"), ("dormir", [], ""),
                                ("salir", [], ""), ("jugar", ["pelota"], " con la pelota")])
    else:
        verbo = rng.choice(list(OBJETOS))
        ob, ot = objeto(verbo, rng)
        v, ot = verbo, " " + ot
    bolsa += ["querer", v] + ob
    texto += f" y quiere {v}{ot}"
    return bolsa, texto


def plantilla_ayuda(rng):
    """Necesito que mi papá me ayude a armar un rompecabezas [porque ...]."""
    p = rng.choice(list(PERSONAS) + list(PERSONAS_CON_ARTICULO))
    ab, at = _accion_simple(rng)
    bolsa = ["necesitar", p, "ayudar"] + ab
    texto = f"necesito que {persona(p)} me ayude a {at}"
    if rng.random() < 0.45:
        mb, mt = rng.choice([(["no", "poder", "solo"], "no puedo solo"),
                             (["ser", "difícil"], "es difícil"),
                             (["no", "saber"], "no sé")])
        bolsa += ["porque"] + mb
        texto += f" porque {mt}"
    return bolsa, texto


def plantilla_gustar(rng):
    """Me gusta mucho jugar al fútbol con mi primo en el club."""
    negar = rng.random() < 0.3
    bolsa = (["no"] if negar else []) + ["gustar"]
    texto = ("no " if negar else "") + "me gusta"
    if not negar and rng.random() < 0.4:
        bolsa.append("mucho")
        texto += " mucho"
    lugar = rng.choice(list(LUGARES))
    verbo, extra, comp = rng.choice(ACTIVIDADES_LUGAR[lugar])
    bolsa += [verbo] + extra
    texto += f" {verbo}" + (f" {comp}" if comp else "")
    if rng.random() < 0.6:
        p = rng.choice(list(PERSONAS))
        bolsa.append(p)
        texto += f" con {persona(p)}"
    bolsa.append(lugar)
    texto += f" {en_lugar(lugar)}"
    if negar and rng.random() < 0.6:
        mb, mt = rng.choice([(["ser", "aburrido"], "es aburrido"), (["ser", "difícil"], "es difícil"),
                             (["tener", "miedo"], "tengo miedo"), (["cansar"], "me canso")])
        bolsa += ["porque"] + mb
        texto += f" porque {mt}"
    return bolsa, texto


VERBOS_PERSONA = ["visitar", "llamar", "abrazar", "ver", "ayudar", "esperar", "saludar"]


def plantilla_persona(rng):
    """Quiero visitar a mi abuela el domingo porque está enferma.
    (el sujeto del motivo es la persona: el adjetivo concuerda con ella)"""
    negar = rng.random() < 0.2
    bolsa, texto = _modal(rng, negar)
    p = rng.choice(list(PERSONAS) + list(PERSONAS_CON_ARTICULO) + ["vecino", "vecina", "padrino", "madrina"])
    verbo = rng.choice(VERBOS_PERSONA)
    ir = not negar and rng.random() < 0.3 and verbo in ("visitar", "ver", "ayudar", "saludar")
    bolsa += (["ir"] if ir else []) + [verbo, p]
    texto += (" ir a" if ir else "") + f" {verbo} {a_persona(p)}"
    t = tiempo(rng)
    if t:
        bolsa += t[0]
        texto = f"{t[1]} {texto}" if t[2] else f"{texto} {t[1]}"
    r = rng.random()
    if r < 0.6:
        g = genero_persona(p)
        if negar:
            mb, mt = rng.choice([(["estar", "enojado"], f"está {flexionar('enojado', g)}"),
                                 (["estar", "ocupado"], f"está {flexionar('ocupado', g)}"),
                                 (["estar", "cansado"], "estoy cansado")])
        else:
            mb, mt = rng.choice([(["estar", "enfermo"], f"está {flexionar('enfermo', g)}"),
                                 (["estar", "triste"], f"está triste"),
                                 (["estar", "solo"], f"está {flexionar('solo', g)}"),
                                 (["ser", "cumpleaños"], "es su cumpleaños"),
                                 (["extrañar", "mucho"], "lo extraño mucho" if g == "m" else "la extraño mucho")])
        bolsa += ["porque"] + mb
        texto += f" porque {mt}"
    return bolsa, texto


# verbo con clítico -> (complementos posibles [(bolsa, texto)], motivos [(bolsa, texto)])
RUTINAS = {
    "acostarme": ([(["cama"], "en la cama"), (["cama", "mamá"], "en la cama de mi mamá")],
                  [(["tener", "sueño"], "tengo sueño"), (["tener", "sueño", "mucho"], "tengo mucho sueño"),
                   (["estar", "cansado"], "estoy cansado"), (["doler", "cabeza"], "me duele la cabeza")]),
    "bañarme": ([(["agua", "caliente"], "con agua caliente"), (["antes", "dormir"], "antes de dormir")],
                [(["estar", "sucio"], "estoy sucio"), (["tener", "calor"], "tengo calor")]),
    "sentarme": ([(["sillón"], "en el sillón"), (["silla"], "en la silla"), (["piso"], "en el piso")],
                 [(["estar", "cansado"], "estoy cansado"), (["doler", "piernas"], "me duelen las piernas"),
                  (["doler", "pies"], "me duelen los pies")]),
    "lavarme": ([(["manos"], "las manos"), (["manos", "antes", "comer"], "las manos antes de comer"),
                 (["dientes"], "los dientes")],
                [(["estar", "sucio"], "estoy sucio"), (["tener", "manos", "sucio"], "tengo las manos sucias")]),
    "cambiarme": ([(["ropa"], "la ropa"), (["remera"], "la remera"), (["zapatillas"], "las zapatillas")],
                  [(["ropa", "estar", "mojado"], "la ropa está mojada"), (["tener", "frío"], "tengo frío"),
                   (["remera", "estar", "sucio"], "la remera está sucia")]),
    "abrigarme": ([(["campera"], "con la campera"), (["bufanda"], "con la bufanda")],
                  [(["tener", "frío"], "tengo frío"), (["hacer", "frío", "mucho"], "hace mucho frío")]),
}


def plantilla_rutina(rng):
    """[tiempo] quiero acostarme en la cama porque tengo mucho sueño.
    / No puedo dormir esta noche porque tengo miedo a la oscuridad."""
    if rng.random() < 0.25:
        bolsa, texto = ["no", "poder", "dormir"], "no puedo dormir"
        t = rng.choice([None, "noche", "anoche"])
        if t == "anoche":
            bolsa, texto = ["anoche", "no", "poder", "dormir"], "anoche no pude dormir"
        elif t:
            bolsa.append(t)
            texto += " esta noche"
        mb, mt = rng.choice([(["tener", "miedo", s], f"tengo miedo {_prep_a(con_articulo(s, g, n, 'def'))}")
                             for s, g, n in MIEDOS] + [(["doler", "panza"], "me duele la panza"),
                                                       (["hacer", "calor", "mucho"], "hace mucho calor")])
        if t == "anoche":
            mt = mt.replace("tengo", "tenía").replace("duele", "dolía").replace("hace", "hacía")
        return bolsa + ["porque"] + mb, f"{texto} porque {mt}"
    verbo = rng.choice(list(RUTINAS))
    comps, motivos = RUTINAS[verbo]
    bolsa, texto = _modal(rng, False)
    bolsa.append(verbo)
    texto += f" {verbo}"
    if rng.random() < 0.7:
        cb, ct = rng.choice(comps)
        bolsa += cb
        texto += f" {ct}"
    t = tiempo(rng)
    if t and t[2]:
        bolsa += t[0]
        texto = f"{t[1]} {texto}"
    mb, mt = rng.choice(motivos)
    return bolsa + ["porque"] + mb, f"{texto} porque {mt}"


PLANTILLAS = [
    (plantilla_ir, 0.18), (plantilla_accion, 0.2), (plantilla_pasado, 0.08),
    (plantilla_dos_acciones, 0.14), (plantilla_sentimiento, 0.08),
    (plantilla_tercera_persona, 0.07), (plantilla_ayuda, 0.05), (plantilla_gustar, 0.05),
    (plantilla_persona, 0.08), (plantilla_rutina, 0.07),
]


def generar(cantidad, seed=7, min_palabras=6, max_palabras=10, excluir=()):
    """Devuelve hasta `cantidad` conceptos (bolsa, frase) distintos, con
    entre `min_palabras` y `max_palabras` palabras de entrada. No repite
    bolsas (como multiconjunto) ni las de `excluir`, para que una misma
    selección del usuario tenga una única frase correcta."""
    rng = random.Random(seed)
    funciones, pesos = zip(*PLANTILLAS)
    vistos = {tuple(sorted(b)) for b in excluir}
    conceptos = []
    intentos = 0
    while len(conceptos) < cantidad and intentos < cantidad * 50:
        intentos += 1
        res = rng.choices(funciones, pesos)[0](rng)
        if res is None:
            continue
        bolsa, texto = res
        if len(set(bolsa)) != len(bolsa) or not (min_palabras <= len(bolsa) <= max_palabras):
            continue
        clave = tuple(sorted(bolsa))
        if clave in vistos:
            continue
        vistos.add(clave)
        if rng.random() < 0.12 and texto.startswith(("quiero", "necesito")) and len(bolsa) < max_palabras:
            bolsa = ["yo"] + bolsa      # el usuario a veces elige "yo": se conserva
            texto = "yo " + texto
        conceptos.append((bolsa, texto[0].upper() + texto[1:] + "."))
    return conceptos
