
frecuencia_palabras = {}


transiciones = {}


historial_frases = []

def registrar_palabra(palabra):
    if palabra in frecuencia_palabras:
        frecuencia_palabras[palabra] += 1
    else:
        frecuencia_palabras[palabra] = 1


def registrar_transicion(palabra_actual, palabra_siguiente):
    if palabra_actual not in transiciones:
        transiciones[palabra_actual] = {}

    if palabra_siguiente in transiciones[palabra_actual]:
        transiciones[palabra_actual][palabra_siguiente] += 1
    else:
        transiciones[palabra_actual][palabra_siguiente] = 1


def procesar_frase(frase):
    for i in range(len(frase)):
        registrar_palabra(frase[i])

        if i < len(frase) - 1:
            registrar_transicion(frase[i], frase[i + 1])

    historial_frases.append(frase)


# Pruebas con datos simulados
"""
procesar_frase(["yo", "quiero", "agua"])
procesar_frase(["yo", "quiero", "ir", "baño"])
procesar_frase(["yo", "quiero", "comida"])
"""
historial_simulado = [
    ["yo", "quiero", "agua"],
    ["yo", "quiero", "ir", "baño"],
    ["quiero", "comida"],
    ["yo", "quiero", "jugar"]
]

for frase in historial_simulado:
    procesar_frase(frase)

print("Frecuencia de palabras:")
print(frecuencia_palabras)

print("\nTransiciones:")
print(transiciones)

print("\nHistorial de frases:")
print(historial_frases)
