"""
Genera scripts/datos/completar_frases.tsv: pares (pictogramas que tocó el
usuario -> frase completa) con los que /corregir aprende a COMPLETAR la frase
a partir de las palabras que el usuario fue eligiendo:

    triste                 -> Estoy triste.
    mamá + agua            -> Mamá, quiero agua.
    pizza                  -> Quiero pizza.
    tengo hambre + pizza   -> Tengo hambre, quiero pizza.
    ayer + pizza           -> Ayer comí pizza.
    hola + chau + pizza    -> Hola chau pizza.      (sin sentido: queda igual)

Regla fundamental: las palabras del usuario aparecen SIEMPRE en la frase, en
su orden y tal cual (un pictograma de varias palabras como "tengo hambre" no
se separa). Solo se AGREGAN palabras antes de cada pictograma ("estoy",
"quiero", ", quiero", "y", "porque", "comer"...). Si la combinación no tiene
ningún sentido, la frase es la misma entrada con mayúscula y punto.

Las frases las arma una gramática chica (ver `completar`). La frase puede
empezar con un saludo, con alguien a quien se llama ("mamá") o con "por
favor", y terminar con "por favor", "gracias" o el nombre. En el medio van
una o dos cláusulas:
    estado      "estoy triste", "estaba bien" (ayer), "voy a estar feliz" (mañana)
    deseo       "quiero pizza, pasta y jugo", "quiero comer pizza y correr",
                "comí pizza" (ayer), "voy a correr" (mañana + actividad)
    ir          "voy a correr", "voy a comer pizza", "voy a estar bien"
    necesidad   "tengo hambre", "tengo sed"
    ser         "yo soy feliz", "vos sos triste"
unidas con ",", "y" o "porque" ("Quiero agua porque tengo sed."), y como
mucho un tiempo ("hoy", "ayer"...) al principio o al final. Lo que no entra
en la gramática se considera sin sentido: tiempos que chocan ("ayer" +
"voy a"), "quiero" sin nada después, estados opuestos ("feliz" + "triste"),
un estado después de otra cláusula ("pizza" + "triste"), un saludo en el
medio, "yo soy" + "pizza"...

Contenido del archivo:
  - TODAS las secuencias de 1, 2 y 3 pictogramas distintos del vocabulario de
    la app (más "mamá" y "papá", que aparecen en los ejemplos), tengan
    sentido o no;
  - TODAS las secuencias de 4 que tienen sentido y una muestra de las que no
    (son 570.024 y casi todas son sin sentido);
  - las mismas frases con otras comidas, bebidas, actividades, estados y
    personas, para que el modelo aprenda la categoría y no cada palabra, y
    palabras sueltas que no se completan ("pelota" -> "Pelota.").

scripts/entrenar_correccion.py entrena el corrector con este archivo además
del corpus.

Uso (desde IA/):  python scripts/dataset_completar.py
"""

import itertools
import os
import random
import sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from correccion import armar_texto  # noqa: E402

SALIDA = os.path.join(AQUI, "datos", "completar_frases.tsv")
SEMILLA = 21
SEPARADOR = " + "            # entre pictogramas en la columna "palabras"

# ── Vocabulario ───────────────────────────────────────────────────────────────

# Pictogramas de la app. Sus palabras nunca se transforman al corregir
# (entrenar_correccion.py las guarda como "palabras_fijas").
VOCABULARIO_APP = [
    "hola", "chau", "bien", "mal", "por favor", "gracias", "ahora", "ayer", "hoy", "mañana",
    "quiero", "tengo hambre", "pizza", "pasta", "jugo", "agua", "gaseosa", "tengo sed", "correr",
    "trabajar", "jugar juegos", "mirar tv", "voy a", "yo soy", "vos sos", "feliz", "triste",
]
# Personas a las que se llama ("Mamá, quiero agua."): no están en la lista de
# la app pero sí en los ejemplos, así que entran en la enumeración completa.
VOCATIVOS = ["mamá", "papá"]

TIEMPO = {"ahora": "pres", "hoy": "pres", "ayer": "pas", "mañana": "fut"}
# estado -> polaridad (no se juntan estados opuestos: "feliz y triste").
POLARIDAD = {"bien": 1, "feliz": 1, "mal": -1, "triste": -1}
ESTADOS_SER = {"feliz", "triste"}            # los que van con "yo soy" / "vos sos"
# actividad -> cómo se dice en pasado ("Ayer fui a correr.").
PASADO = {"correr": "fui a", "trabajar": "fui a", "jugar juegos": "fui a", "mirar tv": "quería"}

CATEGORIA = {"hola": "saludo", "chau": "saludo", "por favor": "cortesia", "gracias": "cortesia",
             "quiero": "quiero", "voy a": "voy_a", "yo soy": "copula", "vos sos": "copula",
             "tengo hambre": "necesidad", "tengo sed": "necesidad",
             "pizza": "comida", "pasta": "comida", "jugo": "bebida", "agua": "bebida",
             "gaseosa": "bebida", "mamá": "vocativo", "papá": "vocativo"}
CATEGORIA.update({p: "tiempo" for p in TIEMPO})
CATEGORIA.update({p: "estado" for p in POLARIDAD})
CATEGORIA.update({p: "actividad" for p in PASADO})

# Vocabulario ampliado: otras palabras de las mismas categorías.
AMPLIADO = {
    "comida": ["helado", "chocolate", "pan", "fruta", "sopa", "arroz", "pollo", "carne", "ensalada",
               "queso", "fideos", "galletitas", "torta", "empanadas", "milanesa", "papas fritas",
               "tostadas", "yogur"],
    "bebida": ["leche", "chocolatada", "mate", "té", "café", "limonada"],
    "actividad": {"nadar": "fui a", "pasear": "fui a", "bailar": "fui a", "jugar a la pelota": "fui a",
                  "andar en bici": "fui a", "dormir": "quería", "dibujar": "quería", "pintar": "quería",
                  "cantar": "quería", "leer": "quería", "descansar": "quería", "cocinar": "quería",
                  "estudiar": "quería", "escuchar música": "quería", "ver dibujitos": "quería",
                  "salir": "quería"},
    # (masculino, femenino, polaridad): en cada frase se usa un solo género.
    "estado": [("contento", "contenta", 1), ("tranquilo", "tranquila", 1), ("mejor", "mejor", 1),
               ("cansado", "cansada", -1), ("enojado", "enojada", -1), ("aburrido", "aburrida", -1),
               ("enfermo", "enferma", -1), ("asustado", "asustada", -1), ("nervioso", "nerviosa", -1)],
    "necesidad": ["tengo frío", "tengo calor", "tengo sueño", "tengo miedo"],
    "vocativo": ["abuela", "abuelo", "seño", "profe", "hermano", "hermana", "tía", "tío"],
}
for _p in AMPLIADO["comida"]:
    CATEGORIA[_p] = "comida"
for _p in AMPLIADO["bebida"]:
    CATEGORIA[_p] = "bebida"
for _p, _pas in AMPLIADO["actividad"].items():
    CATEGORIA[_p] = "actividad"
    PASADO[_p] = _pas
for _m, _f, _pol in AMPLIADO["estado"]:
    for _p in (_m, _f):
        CATEGORIA[_p] = "estado"
        POLARIDAD[_p] = _pol
for _p in AMPLIADO["necesidad"]:
    CATEGORIA[_p] = "necesidad"
for _p in AMPLIADO["vocativo"]:
    CATEGORIA[_p] = "vocativo"

# Palabras sueltas que no se completan: solas no alcanza para deducir nada.
SUELTAS = ["pelota", "perro", "gato", "libro", "auto", "mesa", "silla", "mochila", "lápiz", "árbol",
           "sol", "casa", "escuela", "plaza", "cama", "puerta", "ventana", "zapatillas", "remera",
           "juguete", "bicicleta", "celular", "flor", "parque", "colectivo", "música", "tablet"]

INTERJECCIONES = {"saludo", "cortesia", "vocativo"}
OBJETOS = {"comida", "bebida", "actividad"}

# ── Gramática ─────────────────────────────────────────────────────────────────


def _unir(*partes):
    return " ".join(p for p in partes if p)


def _dividir(elementos):
    """Cuerpo sin el tiempo -> cláusulas {tipo, cabeza, items}. Tipos: N
    (necesidad), C ("yo soy"/"vos sos" + estado), Q ("quiero" + ...), I ("voy
    a" + ...), D (objetos sin "quiero") y E (estados sin verbo)."""
    clausulas = []
    for e in elementos:
        c = CATEGORIA[e]
        actual = clausulas[-1] if clausulas else None
        if c in ("necesidad", "copula", "quiero", "voy_a"):
            tipo = {"necesidad": "N", "copula": "C", "quiero": "Q", "voy_a": "I"}[c]
            clausulas.append({"tipo": tipo, "cabeza": e, "items": []})
            continue
        familia = "estado" if c == "estado" else "objeto" if c in OBJETOS else None
        if familia is None:
            return None
        acepta = {"estado": ("Q", "I", "C", "E"), "objeto": ("Q", "I", "D")}[familia]
        if actual and actual["tipo"] in acepta and all(
                (CATEGORIA[x] == "estado") == (familia == "estado") for x in actual["items"]):
            actual["items"].append(e)
        else:
            clausulas.append({"tipo": "E" if familia == "estado" else "D", "cabeza": None, "items": [e]})
    return clausulas


def _verbo(item, modo):
    c = CATEGORIA[item]
    if modo == "nom":
        return ""
    if modo == "inf":
        return {"comida": "comer", "bebida": "tomar"}.get(c, "")
    return {"comida": "comí", "bebida": "tomé"}.get(c) or PASADO[item]


def _realizar(cl, tiempo):
    """Inserciones de una cláusula (una por elemento: cabeza si hay, después
    los items) y cómo empieza la frase hecha (para validar "chau"), o None."""
    tipo, cabeza, items = cl["tipo"], cl["cabeza"], cl["items"]
    if tipo == "N":
        return ([""], "tengo") if tiempo in (None, "pres") else None
    if not items:
        return None
    if CATEGORIA[items[0]] == "estado":
        if len(items) > 2 or len({POLARIDAD[x] for x in items}) > 1:
            return None
        resto = ["y"] * (len(items) - 1)
        if tipo == "C":
            if tiempo is not None or any(x not in ESTADOS_SER for x in items):
                return None
            return ["", ""] + resto, "ser"
        if tipo in ("Q", "I"):
            if tiempo == "pas":
                return None
            return ["", "estar"] + resto, "voy a" if tipo == "I" else "quiero"
        verbo = {None: "estoy", "pres": "estoy", "pas": "estaba", "fut": "voy a estar"}[tiempo]
        return [verbo] + resto, verbo
    hay_actividad = any(CATEGORIA[x] == "actividad" for x in items)
    if tipo in ("Q", "I"):
        if tiempo == "pas":
            return None
        cabeza_ins, prefijo = [""], ""
        modo = "inf" if hay_actividad or tipo == "I" else "nom"
        empieza = "voy a" if tipo == "I" else "quiero"
    elif tiempo == "pas":
        cabeza_ins, prefijo, modo, empieza = [], "", "pas", "pasado"
    elif tiempo == "fut" and hay_actividad:
        cabeza_ins, prefijo, modo, empieza = [], "voy a", "inf", "voy a"
    else:
        cabeza_ins, prefijo, empieza = [], "quiero", "quiero"
        modo = "inf" if hay_actividad else "nom"
    ins, anterior = [], None
    for k, x in enumerate(items):
        conector = "" if k == 0 else ("y" if k == len(items) - 1 else ",")
        verbo = _verbo(x, modo)
        # "comer pizza, pasta y correr": no se repite el verbo del anterior.
        ins.append(_unir(prefijo if k == 0 else "", conector, "" if verbo == anterior else verbo))
        anterior = verbo
    return cabeza_ins + ins, empieza


# Conector entre dos cláusulas (antes del primer elemento de la segunda).
# Un estado nunca va en la segunda cláusula ("quiero pizza porque estoy
# triste", "tengo sed y estoy mal"): le enseñaba a la red a meter "porque
# estoy" entre cualquier sustantivo y un adjetivo ("quiero agua fría" ->
# "quiero agua porque estoy fría").
UNIONES = {
    ("N", "D"): ",", ("N", "Q"): ",", ("N", "I"): ",", ("N", "N"): "y",
    ("D", "N"): "porque", ("Q", "N"): "porque", ("I", "N"): "porque",
    ("E", "N"): "y", ("E", "D"): "y", ("E", "Q"): "y", ("E", "I"): "y",
    ("D", "Q"): "y", ("D", "I"): "y", ("Q", "I"): "y", ("I", "D"): "y", ("I", "Q"): "y",
}


def _cuerpo(elementos):
    """Inserciones del cuerpo (cláusulas + tiempo) y lo que hace falta para
    validar las interjecciones, o None si no tiene sentido."""
    tiempos = [i for i, e in enumerate(elementos) if CATEGORIA[e] == "tiempo"]
    if len(tiempos) > 1:
        return None
    tiempo, resto = None, list(range(len(elementos)))
    if tiempos:
        if tiempos[0] not in (0, len(elementos) - 1):
            return None
        tiempo = TIEMPO[elementos[tiempos[0]]]
        resto.remove(tiempos[0])
    if not resto:
        return None
    clausulas = _dividir([elementos[i] for i in resto])
    if not clausulas or len(clausulas) > 2:
        return None
    if len(clausulas) == 2:
        tipos = tuple(c["tipo"] for c in clausulas)
        estados_con_verbo = any(c["tipo"] in ("Q", "I") and CATEGORIA[c["items"][0]] == "estado"
                                for c in clausulas if c["items"])
        if tipos not in UNIONES or estados_con_verbo or tiempo not in (None, "pres"):
            return None
    partes = []
    for c in clausulas:
        r = _realizar(c, tiempo)
        if r is None:
            return None
        partes.append(r)
    ins_resto = list(partes[0][0])
    if len(partes) == 2:
        conector = UNIONES[(clausulas[0]["tipo"], clausulas[1]["tipo"])]
        if conector == "y" and "y" in " ".join(partes[0][0]).split():
            conector = ", y"                 # "Quiero pizza y jugo, y voy a correr."
        segunda = list(partes[1][0])
        segunda[0] = _unir(conector, segunda[0])
        ins_resto += segunda
    ins = [""] * len(elementos)
    for i, x in zip(resto, ins_resto):
        ins[i] = x
    primera = clausulas[0]
    unica = len(clausulas) == 1
    return {
        "ins": ins,
        # para "por favor": hay un pedido (algo que se quiere, no en pasado) o solo una necesidad
        "pedido": any(c["tipo"] in ("Q", "D") and c["items"] and CATEGORIA[c["items"][0]] in OBJETOS
                      for c in clausulas) and tiempo != "pas" or (unica and primera["tipo"] == "N"),
        # para "gracias": "estoy bien", "hoy estoy feliz"
        "positivo": unica and primera["tipo"] == "E" and POLARIDAD[primera["items"][0]] == 1
                    and tiempo in (None, "pres"),
        # para "chau": "chau, voy a trabajar"
        "ir": unica and partes[0][1] == "voy a",
    }


def completar(elementos):
    """Inserción antes de cada elemento ("" = nada) para completar la frase,
    o None si la combinación no tiene sentido."""
    n = len(elementos)
    cats = [CATEGORIA[e] for e in elementos]
    cuenta = Counter(cats)
    if cuenta["saludo"] > 1 or cuenta["cortesia"] > 1 or cuenta["vocativo"] > 1:
        return None
    saludo = next((e for e in elementos if CATEGORIA[e] == "saludo"), None)
    cortesia = next((e for e in elementos if CATEGORIA[e] == "cortesia"), None)
    cuerpo = [i for i in range(n) if cats[i] not in INTERJECCIONES]
    # "chau ... mañana" sin nada más -> "Chau, hasta mañana."
    hasta = (len(cuerpo) == 1 and elementos[cuerpo[0]] == "mañana" and cuerpo[0] == n - 1
             and "chau" in elementos)
    if hasta:
        cuerpo = []
    if not cuerpo:
        if n == 1:
            return [""]
        if (saludo == "hola" and cortesia) or (saludo == "chau" and cortesia == "por favor"):
            return None
        # el saludo va primero, salvo "Gracias, chau." y "Mamá, chau."
        if saludo and any(e != "gracias" and CATEGORIA[e] != "vocativo"
                          for e in elementos[:elementos.index(saludo)]):
            return None
        ins = [""] + [","] * (n - 1)
        if hasta:
            ins[-1] = ", hasta"
        return ins
    if cuerpo != list(range(cuerpo[0], cuerpo[-1] + 1)):
        return None                           # interjección en el medio
    if saludo and elementos[0] != saludo:
        return None
    c = _cuerpo([elementos[i] for i in cuerpo])
    if c is None:
        return None
    if saludo == "chau" and not c["ir"]:
        return None
    if cortesia == "por favor" and not c["pedido"]:
        return None
    if cortesia == "gracias" and not c["positivo"]:
        return None
    ins = [""] + [","] * (cuerpo[0] - 1) if cuerpo[0] else []
    ins += c["ins"]
    if cuerpo[0]:
        ins[cuerpo[0]] = _unir(",", ins[cuerpo[0]])
    ins += [","] * (n - cuerpo[-1] - 1)
    return ins


def tokens(elementos, inserciones=None):
    salida = []
    for k, e in enumerate(elementos):
        if inserciones:
            salida += inserciones[k].replace(",", " , ").split()
        salida += e.split()
    return salida


def frase(elementos):
    """(frase, estado): la frase completa, o la misma entrada con mayúscula y
    punto si no tiene sentido. estado: "completada", "ya_completa" (tiene
    sentido sin agregar nada: "Quiero pizza.") o "sin_sentido"."""
    ins = completar(elementos)
    estado = "sin_sentido" if ins is None else ("completada" if any(ins) else "ya_completa")
    return armar_texto(tokens(elementos, ins), "declarativa"), estado


# ── Generación ────────────────────────────────────────────────────────────────

def _ampliar(elementos, rng):
    """Misma secuencia con otras palabras de las mismas categorías."""
    genero = rng.choice((0, 1))
    hay_objetos = any(CATEGORIA[e] in OBJETOS for e in elementos)
    usados, salida = set(elementos), []
    for e in elementos:
        c = CATEGORIA[e]
        opciones = []
        if c in ("comida", "bebida", "vocativo"):
            opciones = AMPLIADO[c]
        elif c == "actividad":
            opciones = list(AMPLIADO["actividad"])
        elif c == "estado":
            opciones = [x[genero] for x in AMPLIADO["estado"] if x[2] == POLARIDAD[e]]
        elif c == "necesidad" and not hay_objetos:   # "quiero agua porque tengo frío" no
            opciones = AMPLIADO["necesidad"]
        opciones = [x for x in opciones if x not in usados]
        if opciones and rng.random() < 0.75:
            e = rng.choice(opciones)
        usados.add(e)
        salida.append(e)
    return tuple(salida)


def generar():
    rng = random.Random(SEMILLA)
    base = VOCABULARIO_APP + VOCATIVOS
    filas = {}                                # secuencia -> (frase, estado)
    for largo in (1, 2, 3):
        for sec in itertools.permutations(base, largo):
            filas[sec] = frase(sec)
    con_sentido, sin_sentido = [], []
    for sec in itertools.permutations(base, 4):
        f, estado = frase(sec)
        (sin_sentido if estado == "sin_sentido" else con_sentido).append((sec, (f, estado)))
    rng.shuffle(sin_sentido)
    filas.update(con_sentido + sin_sentido[:len(con_sentido) // 2])
    n_app = len(filas)
    # Vocabulario ampliado: cada palabra sola, varias variantes de cada
    # secuencia de 1 y 2 pictogramas y variantes de una muestra del resto.
    app = sorted(filas)
    rng.shuffle(app)
    cortas = [s for s in app if len(s) <= 2]
    ampliadas = {(p,): frase((p,)) for p in CATEGORIA if (p,) not in filas}
    for sec in cortas * 4 + app[:30000]:
        nueva = _ampliar(sec, rng)
        if nueva != sec and nueva not in filas:
            ampliadas[nueva] = frase(nueva)
    filas.update(ampliadas)
    for p in SUELTAS:
        filas[(p,)] = (armar_texto(p.split(), "declarativa"), "sin_sentido")
    return filas, n_app


def main():
    filas, n_app = generar()
    orden = sorted(filas, key=lambda s: (len(s), s))
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("palabras\tfrase\n")
        for sec in orden:
            f.write(SEPARADOR.join(sec) + "\t" + filas[sec][0] + "\n")
    estados = Counter(e for _, e in filas.values())
    print(f"{len(filas)} pares -> {SALIDA}")
    print(f"  vocabulario de la app: {n_app} | ampliado y sueltas: {len(filas) - n_app}")
    print(f"  completadas: {estados['completada']} | ya completas: {estados['ya_completa']} | "
          f"sin sentido (quedan iguales): {estados['sin_sentido']}")
    for largo in sorted({len(s) for s in filas}):
        c = Counter(e for s, (_, e) in filas.items() if len(s) == largo)
        print(f"  {largo} pictograma(s): {sum(c.values())} ({c['completada']} completadas, "
              f"{c['ya_completa']} ya completas, {c['sin_sentido']} sin sentido)")
    rng = random.Random(7)
    for sec in rng.sample(orden, 40):
        print(f"   {SEPARADOR.join(sec):50s} -> {filas[sec][0]}")


if __name__ == "__main__":
    main()
