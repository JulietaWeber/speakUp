historial = [
    {
        "categoria": "bebida",
        "fecha": "2026-06-01 08:00",
        "frase": ["quiero", "agua"]
    },
    {
        "categoria": "bebida",
        "fecha": "2026-06-01 08:15",
        "frase": ["quiero", "jugo"]
    },
    {
        "categoria": "comida",
        "fecha": "2026-06-01 13:00",
        "frase": ["quiero", "pizza"]
    }
]

datos_entrenamiento = []

for registro in historial:

    categoria = registro["categoria"]
    frase = registro["frase"]

    for i in range(len(frase) - 1):

        palabra_actual = frase[i]
        palabra_siguiente = frase[i + 1]

        datos_entrenamiento.append(
            (categoria, palabra_actual, palabra_siguiente)
        )

print("Datos de entrenamiento:")
print(datos_entrenamiento)