import bz2
import os
import re
import urllib.request

# Oraciones en español de Tatoeba (https://tatoeba.org, CC BY 2.0 FR). Solo se
# usan para entrenar el corrector (más variedad de estructuras); no van a producción.
URL = "https://downloads.tatoeba.org/exports/per_language/spa/spa_sentences.tsv.bz2"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "datos", "externos")
CRUDO = os.path.join(DESTINO, "spa_sentences.tsv.bz2")
SALIDA = os.path.join(DESTINO, "tatoeba_es.txt")     # una oración por línea

# Solo letras y puntuación básica: sin números ni caracteres raros.
_PERMITIDOS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ¿?¡!,. ]+$")
# Formas de "vosotros" (en Argentina no se usan).
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
    # Mayúscula solo en la primera palabra: descarta los nombres propios del
    # medio (Tatoeba está lleno de "Tom" y "Mary").
    for i, p in enumerate(palabras[1:], start=1):
        if p[0].isupper():
            return False
    return texto[-1] in ".?!"


def main():
    os.makedirs(DESTINO, exist_ok=True)
    if not os.path.exists(CRUDO):            # el .bz2 se descarga una sola vez
        print(f"Descargando {URL} ...")
        urllib.request.urlretrieve(URL, CRUDO)
    # Cada línea es id, idioma y texto: se guardan las oraciones válidas sin repetir.
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


# Uso (desde IA/): python -I scripts/descargar_tatoeba.py
if __name__ == "__main__":
    main()
