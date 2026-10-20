"""
Prueba de punta a punta de todos los endpoints de la API (con el TestClient de
FastAPI, sin levantar un servidor).

- /predecir: 36+ contextos de 1, 2 y 3 palabras sacados de frases que NO están
  en ningún dataset de entrenamiento. Verifica que siempre vuelvan 3 palabras
  distintas con probabilidad, ordenadas, y en menos de 100 ms.
- /corregir: 30+ frases casi correctas que NO están en los datasets. Verifica
  que la respuesta llegue en menos de 2 s, que no se reordene ni se invente
  ninguna palabra de contenido, y la compara con la corrección esperada.
- /reentrenar, / y /ping.

Uso (desde IA/):  python scripts/probar_endpoints.py
Sale con código 1 si falla algún chequeo obligatorio.
"""

import os
import re
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
os.environ["SPEAKUP_DIR_USUARIOS"] = tempfile.mkdtemp(prefix="speakup_test_")

from fastapi.testclient import TestClient  # noqa: E402

from morfologia import quitar_tildes  # noqa: E402

T0 = time.time()
import api  # noqa: E402

print(f"API cargada en {time.time() - T0:.1f}s")
cliente = TestClient(api.app)

_PAL = re.compile(r"[a-záéíóúüñ]+")


def palabras(texto):
    return _PAL.findall(texto.lower())


def corpus_entrenamiento():
    frases = set()
    for ruta in ("datos/corpus_caa.txt", "datos/frases_curadas.txt", "datos/externos/tatoeba_es.txt"):
        ruta = os.path.join(AQUI, ruta)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                for linea in f:
                    frases.add(" ".join(palabras(linea)))
    return frases


CORPUS = corpus_entrenamiento()
TEXTO_CORPUS = "\n".join(CORPUS)


def en_corpus(texto):
    return (" ".join(palabras(texto))) in CORPUS


fallas = []


def chequear(condicion, mensaje):
    if not condicion:
        fallas.append(mensaje)
        print("   FALLA:", mensaje)


# ── / y /ping ─────────────────────────────────────────────────────────────────

print("\n== GET / y /ping ==")
for ruta in ("/", "/ping"):
    r = cliente.get(ruta)
    print(f"{ruta} -> {r.status_code} {r.json()}")
    chequear(r.status_code == 200 and r.json() == {"status": "ok"}, f"{ruta} no responde ok")

# ── /predecir ─────────────────────────────────────────────────────────────────

FRASES_PREDICCION = [
    "mañana quiero visitar a mi madrina",
    "me duele mucho la muela de abajo",
    "necesito que me ayudes con el uniforme",
    "mi abuela está cocinando ñoquis",
    "tengo ganas de ir a la pileta del club",
    "no quiero tomar el jarabe",
    "quiero jugar a la play con mi primo",
    "estoy cansado de esperar el colectivo",
    "vamos a comprar figuritas al kiosco",
    "mi perro se escapó de casa",
    "puedo comer otra porción de torta",
    "la seño nos llevó al museo",
]

print("\n== POST /predecir ==")
contextos = []
for frase in FRASES_PREDICCION:
    chequear(not en_corpus(frase), f"la frase de prueba '{frase}' está en el corpus")
    toks = frase.split()
    for n in (1, 2, 3):
        contextos.append(toks[:n])
    contextos.append(toks[-4:-1])   # ventana del medio/final de la frase
contextos += [[], ["xyzzy"], ["QUIERO", "Ir"], ["por favor"], ["Mamá"], ["string", "string", "string"]]

tiempos = []
nuevos3 = 0
for ctx in contextos:
    t = time.perf_counter()
    r = cliente.post("/predecir", json={"user_id": "prueba", "palabras": ctx})
    ms = (time.perf_counter() - t) * 1000
    tiempos.append(ms)
    res = r.json()
    ok = (r.status_code == 200 and isinstance(res, list) and len(res) == 3
          and all(isinstance(x.get("palabra"), str) and x["palabra"] for x in res)
          and all(isinstance(x.get("probabilidad"), (int, float)) and 0 <= x["probabilidad"] <= 100 for x in res)
          and len({x["palabra"] for x in res}) == 3
          and [x["probabilidad"] for x in res] == sorted([x["probabilidad"] for x in res], reverse=True))
    chequear(ok, f"/predecir {ctx} devolvió {res}")
    chequear(ms < 100, f"/predecir {ctx} tardó {ms:.1f} ms")
    nuevo = len(ctx) == 3 and (" " + " ".join(ctx).lower() + " ") not in (" " + TEXTO_CORPUS.replace("\n", " \n ") + " ")
    nuevos3 += nuevo
    marca = " [contexto de 3 nunca visto]" if nuevo else ""
    print(f"{str(ctx):45s} {ms:6.1f} ms  " + ", ".join(f"{x['palabra']} ({x['probabilidad']}%)" for x in res) + marca)

# Formato exacto que manda el back (ejemplo de Swagger).
r = cliente.post("/predecir", json={"user_id": "string", "palabras": ["string", "string", "string"]})
chequear(r.status_code == 200 and len(r.json()) == 3, "formato del back {'user_id','palabras'} no funciona")
r = cliente.post("/predecir", json={"user_id": "prueba"})
chequear(r.status_code == 200 and len(r.json()) == 3, "sin 'palabras' debería predecir el inicio de frase")
r = cliente.post("/predecir", json={"palabras": ["hola"]})
chequear(r.status_code == 422, "sin user_id debería dar 422")
print(f"Contextos probados: {len(contextos)} | de 3 palabras nunca vistos: {nuevos3} | "
      f"tiempo máx {max(tiempos):.1f} ms, promedio {sum(tiempos) / len(tiempos):.1f} ms")

# ── /reentrenar ───────────────────────────────────────────────────────────────

print("\n== POST /reentrenar ==")
antes = cliente.post("/predecir", json={"user_id": "u_test", "palabras": ["quiero", "ir", "a"]}).json()
r = cliente.post("/reentrenar", json={"user_id": "u_test", "datos": [
    {"categoria": "Casa", "frase": ["quiero", "ir", "a", "lo", "de", "Marta"]},
    {"categoria": "Casa", "frase": ["quiero", "ir", "a", "lo", "de", "Marta", "mañana"]},
    {"frase": ["quiero", "ir", "a", "lo", "de", "Marta"]},
]})
print("reentrenar ->", r.json())
chequear(r.status_code == 200 and r.json().get("status") == "ok", "reentrenar no devolvió ok")
despues = cliente.post("/predecir", json={"user_id": "u_test", "palabras": ["quiero", "ir", "a"]}).json()
print("antes  :", antes)
print("después:", despues)
chequear(despues[0]["palabra"] == "lo", "después de reentrenar, 'lo' debería ser la primera sugerencia")
otra = cliente.post("/predecir", json={"user_id": "u_test", "palabras": ["lo", "de"]}).json()
print("['lo','de'] ->", otra)
chequear(any(x["palabra"] == "marta" for x in otra), "la palabra nueva del usuario ('marta') debería sugerirse")
r = cliente.post("/reentrenar", json={"user_id": "u_test", "datos": []})
chequear(r.json() == {"status": "sin_datos"}, "datos vacíos deberían dar sin_datos")
dir_usuarios = os.environ["SPEAKUP_DIR_USUARIOS"]
fuera = os.path.join(os.path.dirname(dir_usuarios), "malicioso.json")
r = cliente.post("/reentrenar", json={"user_id": "../malicioso", "datos": [{"frase": ["hola", "mamá"]}]})
archivos = os.listdir(dir_usuarios)
print("archivos de usuarios:", archivos)
chequear(r.status_code == 200 and not os.path.exists(fuera) and any("malicioso" in a for a in archivos),
         "user_id con '../' no debería escribir fuera de la carpeta de usuarios")

# ── /corregir ─────────────────────────────────────────────────────────────────

# (entrada, salidas aceptables)
CASOS_CORRECCION = [
    ("mañana quiero ir parque con mi tía Rosa", ["Mañana quiero ir al parque con mi tía Rosa."]),
    ("me duele cabeza desde la mañana", ["Me duele la cabeza desde la mañana."]),
    ("mi mamá está cansado porque trabajó mucho", ["Mi mamá está cansada porque trabajó mucho."]),
    ("necesito ayuda con tarea de matemática", ["Necesito ayuda con la tarea de matemática."]),
    ("la perro de mi vecina ladra mucho", ["El perro de mi vecina ladra mucho."]),
    ("yo quiere comer una milanesa con papas", ["Yo quiero comer una milanesa con papas."]),
    ("donde esta mi campera azul", ["¿Dónde está mi campera azul?"]),
    ("quiero agua fría por favor", ["Quiero agua fría, por favor."]),
    ("ayer fui a el médico con mi papá", ["Ayer fui al médico con mi papá."]),
    ("los chicos juega en el patio de la escuela", ["Los chicos juegan en el patio de la escuela."]),
    ("mamá quiero ver dibujitos en la tele", ["Mamá, quiero ver dibujitos en la tele."]),
    ("estoy muy contenta porque mañana viene mi abuela", ["Estoy muy contenta porque mañana viene mi abuela."]),
    ("tengo mucho hambre y quiero merendar", ["Tengo mucha hambre y quiero merendar."]),
    ("el sábado vamos ir a la casa de mis primos", ["El sábado vamos a ir a la casa de mis primos."]),
    ("me gusta mucho jugar a la pelota con mi hermano", ["Me gusta mucho jugar a la pelota con mi hermano."]),
    ("quiero que vos vengas a mi cumpleaños", ["Quiero que vos vengas a mi cumpleaños."]),
    ("mi hermana tiene una muñeca nuevo", ["Mi hermana tiene una muñeca nueva."]),
    ("no quiero ir escuela hoy porque estoy enfermo", ["No quiero ir a la escuela hoy porque estoy enfermo."]),
    ("la maestra me felicitó porque hice tarea", ["La maestra me felicitó porque hice la tarea."]),
    ("podés prender luz", ["¿Podés prender la luz?", "Podés prender la luz."]),
    ("quiero un vaso agua", ["Quiero un vaso de agua."]),
    ("mis zapatillas están sucio", ["Mis zapatillas están sucias."]),
    ("hoy comí fideos con queso en lo de mi abuela", ["Hoy comí fideos con queso en lo de mi abuela."]),
    ("el colectivo tarda mucho y tengo frio", ["El colectivo tarda mucho y tengo frío."]),
    ("quiero ir al plaza con mi perro", ["Quiero ir a la plaza con mi perro."]),
    ("mi papa esta trabajando en la oficina", ["Mi papá está trabajando en la oficina."]),
    ("nosotros fue al cine el domingo", ["Nosotros fuimos al cine el domingo."]),
    ("me duelen la panza", ["Me duele la panza."]),
    ("quiero jugar con la tablet un rato mas", ["Quiero jugar con la tablet un rato más."]),
    ("gracias por ayudarme con la mochila", ["Gracias por ayudarme con la mochila."]),
    ("tengo turno con dentista el lunes", ["Tengo turno con el dentista el lunes."]),
    ("vamos a la plaza despues de comer", ["Vamos a la plaza después de comer."]),
    ("mi abuelo me regaló un auto rojo", ["Mi abuelo me regaló un auto rojo."]),
    ("estoy triste porque se rompió mi bici", ["Estoy triste porque se rompió mi bici."]),
]

FUNCIONALES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "al", "del", "lo", "a", "de", "en", "con",
    "para", "por", "que", "y", "e", "o", "u", "me", "te", "se", "le", "mi", "mis", "nos",
}


def raiz(w):
    return quitar_tildes(w)[:3]


def respeta_entrada(entrada, salida):
    """La salida tiene las palabras de contenido de la entrada, en el mismo
    orden (se permite otra forma de la misma palabra: misma raíz de 3
    letras), y todo lo agregado es una palabra funcional."""
    ent = palabras(entrada)
    sal = palabras(salida)
    i = 0
    for w in sal:
        if i < len(ent) and (w == ent[i] or raiz(w) == raiz(ent[i])
                             or (ent[i] in ("al", "del") and w in ("a", "de"))):
            i += 1
        elif i > 0 and ent[i - 1] in ("al", "del") and w in ("la", "los", "las"):
            continue
        elif w in FUNCIONALES:
            continue
        else:
            return False
    resto = [w for w in ent[i:] if w not in FUNCIONALES]
    return not resto


print("\n== POST /corregir ==")
exactas = 0
tiempos = []
for entrada, esperadas in CASOS_CORRECCION:
    chequear(not en_corpus(esperadas[0]), f"la frase de prueba '{esperadas[0]}' está en el corpus")
    t = time.perf_counter()
    r = cliente.post("/corregir", json={"palabras": entrada.split()})
    ms = (time.perf_counter() - t) * 1000
    tiempos.append(ms)
    frase = r.json().get("frase", "")
    ok = frase in esperadas
    exactas += ok
    chequear(r.status_code == 200 and frase, f"/corregir {entrada!r} no devolvió frase")
    chequear(ms < 2000, f"/corregir {entrada!r} tardó {ms:.0f} ms")
    chequear(respeta_entrada(entrada, frase), f"/corregir {entrada!r} cambió/inventó palabras: {frase!r}")
    print(f"{'OK ' if ok else '-- '} {ms:5.0f} ms  {entrada!r:55s} -> {frase!r}" + ("" if ok else f"   (esperado: {esperadas[0]!r})"))

for especial, esperado in [([], ""), (["agua"], "agua"), (["  ", ""], ""), (["por favor"], None),
                           (["Quiero", "ir", "al", "baño", "?"], None), ([1, "hola"], None)]:
    r = cliente.post("/corregir", json={"palabras": especial})
    print(f"   especial {especial!r} -> {r.status_code} {r.json()}")
    chequear(r.status_code == 200, f"/corregir {especial!r} dio {r.status_code}")
    if esperado is not None:
        chequear(r.json().get("frase") == esperado, f"/corregir {especial!r} debería dar {esperado!r}")

print(f"\nCorrecciones iguales a la esperada: {exactas}/{len(CASOS_CORRECCION)} | "
      f"tiempo máx {max(tiempos):.0f} ms, promedio {sum(tiempos) / len(tiempos):.0f} ms")

print("\n" + ("TODOS LOS CHEQUEOS OBLIGATORIOS PASARON" if not fallas else f"{len(fallas)} FALLAS:"))
for f in fallas:
    print(" -", f)
sys.exit(1 if fallas else 0)
