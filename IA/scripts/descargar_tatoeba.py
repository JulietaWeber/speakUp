"""
Descarga las oraciones en español de Tatoeba (https://tatoeba.org, licencia
CC BY 2.0 FR) y guarda un subconjunto filtrado en
scripts/datos/externos/tatoeba_es.txt (una oración por línea).

Se usan SOLO para entrenar el corrector (scripts/entrenar_correccion.py):
aportan variedad de estructuras reales del español (artículos, preposiciones,
concordancia) que las plantillas de CAA no cubren. No se usan en producción.

Filtros: oraciones de 3 a 14 palabras, sin números, sin nombres propios en el
medio de la oración (Tatoeba está lleno de "Tom" y "Mary"), sin formas de
"vosotros" (en Argentina no se usan) y sin caracteres raros.

Uso (desde IA/):  python -I scripts/descargar_tatoeba.py
"""

import bz2
import os
import re
import urllib.request

URL = "https://downloads.tatoeba.org/exports/per_language/spa/spa_sentences.tsv.bz2"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "datos", "externos")
CRUDO = os.path.join(DESTINO, "spa_sentences.tsv.bz2")
SALIDA = os.path.join(DESTINO, "tatoeba_es.txt")

_PERMITIDOS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ¿?¡!,. ]+$")
_VOSOTROS = re.compile(
    r"\b(vosotros|vosotras|os|vuestro|vuestra|vuestros|vuestras|\w+áis|\w+éis|\w+aos)\b",
    re.IGNORECASE,
)


def oracion_valida(texto):
    if not _PERMITIDOS.match(texto) or _VOSOTROS.search(texto):
        return False
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", texto)
    if not 3 <= len(palabras) <= 14:
        return False
    # Mayúscula solo al principio o después de un signo de apertura/punto.
    for i, p in enumerate(palabras[1:], start=1):
        if p[0].isupper():
            return False
    return texto[-1] in ".?!"


def main():
    os.makedirs(DESTINO, exist_ok=True)
    if not os.path.exists(CRUDO):
        print(f"Descargando {URL} ...")
        urllib.request.urlretrieve(URL, CRUDO)
    vistas, total = set(), 0
    with bz2.open(CRUDO, "rt", encoding="utf-8") as f, open(SALIDA, "w", encoding="utf-8") as out:
        for linea in f:
            partes = linea.rstrip("\n").split("\t")
            if len(partes) < 3:
                continue
            texto = partes[2].strip()
            total += 1
            if texto in vistas or not oracion_valida(texto):
                continue
            vistas.add(texto)
            out.write(texto + "\n")
    print(f"Oraciones leídas: {total} | guardadas: {len(vistas)} -> {SALIDA}")


if __name__ == "__main__":
    main()
