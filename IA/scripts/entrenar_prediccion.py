import json
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from prediccion import INICIO, MAX_CONTEXTO, tokenizar  # noqa: E402

# Corpus (archivo, peso): las frases generadas (corpus_caa.py) y las escritas
# a mano, que cuentan 3 veces.
FUENTES = [
    (os.path.join(AQUI, "datos", "corpus_caa.txt"), 1),
    (os.path.join(AQUI, "datos", "frases_curadas.txt"), 3),
]
# Modelo de /predecir que carga prediccion.py.
SALIDA_NPZ = os.path.join(RAIZ, "modelo_prediccion.npz")
SALIDA_JSON = os.path.join(RAIZ, "modelo_prediccion.json")
ORDEN = MAX_CONTEXTO + 1   # 4-gramas


def leer_frases():
    frases = []
    for ruta, peso in FUENTES:
        with open(ruta, encoding="utf-8") as f:
            lineas = [l.strip() for l in f if l.strip()]
        for linea in lineas:
            toks = tokenizar(linea)
            if toks:
                frases.extend([toks] * peso)
        print(f"{os.path.basename(ruta)}: {len(lineas)} frases (peso {peso})")
    return frases


def contar(frases):
    """Conteos crudos de n-gramas (1..ORDEN) con un <s> al inicio."""
    conteos = [Counter() for _ in range(ORDEN + 1)]
    for toks in frases:
        # <s> permite predecir el principio de la frase ("<s> quiero" -> "ir").
        seq = [INICIO] + toks
        for n in range(1, ORDEN + 1):
            for i in range(len(seq) - n + 1):
                ng = tuple(seq[i:i + n])
                if ng[-1] == INICIO:
                    continue
                conteos[n][ng] += 1
    return conteos


def conteos_kn(conteos):
    """Conteos efectivos de Kneser-Ney: crudos en el orden máximo y en los
    n-gramas que empiezan con <s> (no se pueden extender a la izquierda);
    de continuación (cuántas palabras distintas los preceden) en el resto."""
    efectivos = [Counter() for _ in range(ORDEN + 1)]
    for ng, c in conteos[ORDEN].items():
        efectivos[ORDEN][ng] = c
    for n in range(2, ORDEN + 1):
        for ng in conteos[n]:
            efectivos[n - 1][ng[1:]] += 1      # continuación de ng[1:]
    for n in range(1, ORDEN):
        for ng, c in conteos[n].items():
            if ng[0] == INICIO:
                efectivos[n][ng] = c
    return efectivos


def descuento(cuenta):
    """D = n1 / (n1 + 2 n2) (estimación de Ney)."""
    valores = Counter(cuenta.values())
    n1, n2 = valores.get(1, 0), valores.get(2, 0)
    return n1 / (n1 + 2 * n2) if n1 + n2 else 0.75


def main():
    # n-gramas de hasta 4 palabras con suavizado Kneser-Ney interpolado.
    frases = leer_frases()
    conteos = contar(frases)
    efectivos = conteos_kn(conteos)

    vocab = sorted({ng[0] for ng in conteos[1]})
    idx = {w: i for i, w in enumerate(vocab)}
    print(f"Vocabulario: {len(vocab)} palabras | 4-gramas: {len(conteos[4])}")

    # Unigrama de continuación (sin <s>, que nunca se predice).
    uni = np.zeros(len(vocab), dtype=np.float64)
    for (w,), c in efectivos[1].items():
        uni[idx[w]] = c
    uni = 0.98 * uni / uni.sum() + 0.02 / len(vocab)

    # Por cada contexto h (1..3 palabras): entradas (w, max(c-D,0)/c(h)) y
    # gamma(h) = D * N1+(h·) / c(h), el peso del contexto más corto. Así un
    # contexto nunca visto ("mañana vamos a") se predice por sus partes ("vamos a").
    claves, gammas, indptr, indices, valores = [], [], [0], [], []
    descuentos = {}
    for n in range(2, ORDEN + 1):
        D = descuento(efectivos[n])
        descuentos[n] = D
        por_contexto = defaultdict(list)
        for ng, c in efectivos[n].items():
            por_contexto[ng[:-1]].append((ng[-1], c))
        for h in sorted(por_contexto):
            entradas = por_contexto[h]
            total = sum(c for _, c in entradas)
            claves.append(" ".join(h))
            gammas.append(D * len(entradas) / total)
            for w, c in sorted(entradas):
                indices.append(idx[w])
                valores.append(max(c - D, 0.0) / total)
            indptr.append(len(indices))
    print(f"Contextos: {len(claves)} | entradas: {len(indices)} | descuentos: "
          + ", ".join(f"{n}-gr={d:.2f}" for n, d in descuentos.items()))

    # Matriz dispersa contextos x palabras (CSR) en el .npz; los textos en el .json.
    np.savez_compressed(
        SALIDA_NPZ,
        unigrama=uni.astype(np.float32),
        gamma=np.array(gammas, dtype=np.float32),
        indptr=np.array(indptr, dtype=np.int32),
        indices=np.array(indices, dtype=np.int32),
        valores=np.array(valores, dtype=np.float32),
    )
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump({"vocab": vocab, "contextos": claves, "orden": ORDEN}, f, ensure_ascii=False)
    print(f"Guardado: {SALIDA_NPZ} ({os.path.getsize(SALIDA_NPZ) // 1024} KB), "
          f"{SALIDA_JSON} ({os.path.getsize(SALIDA_JSON) // 1024} KB)")


# Uso (desde IA/): python scripts/entrenar_prediccion.py
if __name__ == "__main__":
    main()
