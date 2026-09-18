"""
Genera dataset_correccion.jsonl: pares (palabras sueltas -> frase natural
correcta) para entrenar modelo_correccion.py.

Los conceptos base (bolsa de palabras + frase correcta) viven en
conceptos_correccion.jsonl. La regla que tiene que cumplir cada uno, para
que el modelo aprenda a NO inventar contenido, es: la frase de salida solo
puede usar (a) palabras funcionales cerradas (artículos, preposiciones,
pronombres, posesivos, demostrativos, conjunciones - ver gramatica.py) o
(b) palabras derivadas de las que están en la bolsa de entrada (reordenadas,
conjugadas, en singular/plural). Cualquier concepto que no cumpla esto se
descarta automáticamente acá, como red de seguridad ante ediciones futuras.

Para cada concepto válido generamos varias permutaciones del orden de las
palabras de entrada, porque en la vida real el usuario de CAA selecciona los
botones en cualquier orden: eso le enseña al modelo a ser invariante al
orden de entrada.
"""

import json
import random
import re

import spacy

from gramatica import lema, es_permitida

random.seed(42)

MAX_PERMS_POR_CONCEPTO = 8

RUTA_CONCEPTOS = "conceptos_correccion.jsonl"
RUTA_DATASET_GENERADO = "dataset_correccion.jsonl"


def tokenizar_salida(texto):
    return re.findall(r"\w+|[^\w\s]", texto, flags=re.UNICODE)


def cargar_conceptos(ruta):
    conceptos = []
    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            par = json.loads(linea)
            conceptos.append((par["input"].split(), par["output"]))
    return conceptos


def concepto_valido(nlp, bag, frase):
    lemas_entrada = {lema(nlp, p) for p in bag}
    return all(es_permitida(nlp, t, lemas_entrada) for t in tokenizar_salida(frase))


def generar_permutaciones(bag, k):
    """Hasta k permutaciones distintas del orden de las palabras (al azar en
    vez de con itertools, que para bags largos sería carísimo)."""
    resultados = []
    vistos = set()
    max_intentos = k * 25
    intentos = 0
    while len(resultados) < k and intentos < max_intentos:
        intentos += 1
        perm = tuple(random.sample(bag, len(bag)))
        if perm in vistos:
            continue
        vistos.add(perm)
        resultados.append(perm)
    return resultados


def main():
    print("Cargando spaCy para validar los conceptos...")
    nlp = spacy.load("es_core_news_md")

    conceptos = cargar_conceptos(RUTA_CONCEPTOS)
    print(f"Conceptos cargados: {len(conceptos)}")

    validos = []
    for bag, frase in conceptos:
        if concepto_valido(nlp, bag, frase):
            validos.append((bag, frase))
        else:
            print(f"AVISO: concepto descartado por inventar contenido: {bag} -> {frase!r}")
    print(f"Conceptos válidos: {len(validos)}\n")

    pares_finales = []
    for bag, frase in validos:
        perms = generar_permutaciones(bag, MAX_PERMS_POR_CONCEPTO)
        for perm in perms:
            pares_finales.append({"input": " ".join(perm), "output": frase})

    random.shuffle(pares_finales)

    print(f"Pares generados (con permutaciones): {len(pares_finales)}")

    with open(RUTA_DATASET_GENERADO, "w", encoding="utf-8") as f:
        for par in pares_finales:
            f.write(json.dumps(par, ensure_ascii=False) + "\n")

    print(f"Guardado en: {RUTA_DATASET_GENERADO}")


if __name__ == "__main__":
    main()
