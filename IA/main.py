
frecuencia_palabras = {}


transiciones = {}


historial_frases = []

def registrar_palabra(palabra):
    if palabra in frecuencia_palabras:
        frecuencia_palabras[palabra] += 1
    else:
        frecuencia_palabras[palabra] = 1
