"""
Genera dataset_correccion.jsonl: pares (palabras sueltas -> frase natural correcta)
para entrenar modelo_correccion.py.

Estrategia: partimos de "conceptos" (bolsa de palabras + frase correcta) y generamos
varias permutaciones del orden de las palabras para cada concepto, porque en la vida
real el usuario de CAA selecciona los botones en cualquier orden. Esto también le
enseña al modelo a ser invariante al orden de entrada, que es la generalización que
más nos importa.
"""

import json
import random
import itertools
import os

random.seed(42)

MAX_PERMS_POR_CONCEPTO = 6

# ── 1) Reusar el dataset ya armado (300 conceptos, 50 por categoría) ───────────

RUTA_DATASET_BASE = os.path.join("IA LLM", "dataset_caa.jsonl")

conceptos = []  # lista de (bag_de_palabras: list[str], frase_correcta: str)

with open(RUTA_DATASET_BASE, "r", encoding="utf-8") as f:
    for linea in f:
        par = json.loads(linea)
        bag = par["input"].split()
        conceptos.append((bag, par["output"]))

# ── 2) Conceptos nuevos (situaciones adicionales, ~12 por categoría) ───────────

conceptos_nuevos = [
    # Casa
    (["querer", "comer", "postre"], "Quiero comer un postre."),
    (["necesitar", "cambiar", "ropa", "mojada"], "Necesito cambiarme la ropa mojada."),
    (["querer", "ayudar", "hermano", "tarea"], "Quiero ayudar a mi hermano con la tarea."),
    (["no", "querer", "compartir", "juguete"], "No quiero compartir el juguete."),
    (["querer", "prender", "computadora"], "Quiero prender la computadora."),
    (["necesitar", "pilas", "control"], "Necesito pilas para el control remoto."),
    (["querer", "sentarme", "sillón"], "Quiero sentarme en el sillón."),
    (["hermano", "molestar", "yo"], "Mi hermano me está molestando."),
    (["querer", "ordenar", "juguetes"], "Quiero ordenar mis juguetes."),
    (["necesitar", "agua", "planta"], "Necesito regar la planta con agua."),
    (["querer", "helado", "heladera"], "Quiero un helado de la heladera."),
    (["mamá", "trabajar", "no", "molestar"], "Mamá está trabajando, no quiero molestarla."),
    # Escuela
    (["querer", "cambiar", "grupo"], "Quiero cambiarme de grupo."),
    (["necesitar", "hoja", "carpeta"], "Necesito una hoja de la carpeta."),
    (["querer", "presentar", "proyecto"], "Quiero presentar mi proyecto."),
    (["maestra", "felicitar", "yo"], "La maestra me felicitó."),
    (["querer", "sentarme", "amigo", "lado"], "Quiero sentarme al lado de mi amigo."),
    (["no", "entender", "tarea", "matemática"], "No entiendo la tarea de matemática."),
    (["querer", "salir", "excursión"], "Quiero ir a la excursión."),
    (["necesitar", "firmar", "cuaderno"], "Necesito que firmen el cuaderno."),
    (["querer", "cambiar", "asiento"], "Quiero cambiarme de asiento."),
    (["olvidé", "educación física", "ropa"], "Olvidé la ropa de educación física."),
    (["querer", "ir", "casa", "temprano"], "Quiero irme a casa temprano."),
    (["compañero", "compartir", "lápiz"], "Un compañero me prestó un lápiz."),
    # Médico
    (["necesitar", "curita", "rodilla"], "Necesito una curita en la rodilla."),
    (["tener", "tos", "fuerte"], "Tengo mucha tos."),
    (["querer", "saber", "resultado", "análisis"], "Quiero saber el resultado del análisis."),
    (["doler", "cuello"], "Me duele el cuello."),
    (["necesitar", "vacuna"], "Necesito ponerme la vacuna."),
    (["tener", "picazón", "brazo"], "Tengo picazón en el brazo."),
    (["querer", "ir", "casa", "enfermo"], "Estoy enfermo y quiero ir a casa."),
    (["necesitar", "reposo"], "Necesito hacer reposo."),
    (["doctora", "revisar", "oído"], "La doctora me va a revisar el oído."),
    (["necesitar", "termómetro"], "Necesito el termómetro."),
    (["tener", "tos", "no", "parar"], "Tengo tos y no para."),
    (["querer", "mamá", "quedarse", "conmigo"], "Quiero que mamá se quede conmigo."),
    # Emociones
    (["estar", "agradecido"], "Estoy agradecido."),
    (["sentir", "envidia"], "Siento envidia."),
    (["estar", "entusiasmado", "viaje"], "Estoy entusiasmado por el viaje."),
    (["sentir", "alivio"], "Siento alivio."),
    (["estar", "decepcionado"], "Estoy decepcionado."),
    (["necesitar", "espacio", "solo"], "Necesito espacio para estar solo."),
    (["sentir", "culpa"], "Siento culpa."),
    (["estar", "orgulloso", "mí", "mismo"], "Estoy orgulloso de mí mismo."),
    (["querer", "gritar", "feliz"], "Estoy tan feliz que quiero gritar."),
    (["no", "saber", "qué", "sentir"], "No sé qué estoy sintiendo."),
    (["sentir", "calma", "música"], "La música me hace sentir calma."),
    (["estar", "asustado", "ruido"], "Ese ruido me asustó."),
    # Transporte
    (["querer", "bajar", "próxima", "parada"], "Quiero bajar en la próxima parada."),
    (["colectivo", "no", "parar"], "El colectivo no paró."),
    (["necesitar", "ayuda", "subir", "escalón"], "Necesito ayuda para subir el escalón."),
    (["querer", "ventanilla", "abierta"], "Quiero la ventanilla abierta."),
    (["falta", "mucho", "llegar"], "¿Falta mucho para llegar?"),
    (["necesitar", "bajar", "urgente"], "Necesito bajar urgente."),
    (["querer", "ir", "adelante", "auto"], "Quiero ir adelante en el auto."),
    (["mareado", "colectivo", "ventana"], "Estoy mareado, necesito la ventana abierta."),
    (["chofer", "esperar", "yo"], "Necesito que el chofer me espere."),
    (["querer", "escuchar", "música", "viaje"], "Quiero escuchar música durante el viaje."),
    (["necesitar", "ir", "baño", "viaje"], "Necesito ir al baño durante el viaje."),
    (["auto", "estacionar", "lejos"], "El auto quedó estacionado lejos."),
    # Amigos
    (["amigo", "cumpleaños", "regalo", "querer"], "Quiero comprarle un regalo a mi amigo por su cumpleaños."),
    (["querer", "perdonar", "amigo"], "Quiero perdonar a mi amigo."),
    (["amigo", "invitar", "casa"], "Quiero invitar a mi amigo a casa."),
    (["extrañar", "amigo", "otra", "ciudad"], "Extraño a mi amigo que vive en otra ciudad."),
    (["amigo", "no", "querer", "jugar"], "Mi amigo no quiere jugar conmigo."),
    (["querer", "hacer", "las", "paces"], "Quiero hacer las paces con mi amigo."),
    (["amigo", "contarme", "secreto"], "Mi amigo me contó un secreto."),
    (["querer", "presentar", "amigo", "nuevo"], "Quiero presentarte a mi amigo nuevo."),
    (["amigo", "defenderme"], "Mi amigo me defendió."),
    (["querer", "juntarme", "amigos", "fin", "semana"], "Quiero juntarme con mis amigos el fin de semana."),
    (["amigo", "copiarse", "prueba"], "Mi amigo se copió en la prueba."),
    (["amigo", "ayudar", "mudanza"], "Quiero ayudar a mi amigo con la mudanza."),
]

conceptos.extend(conceptos_nuevos)

# ── 2b) Pedidos dirigidos a mamá/papá y combinaciones emoción+tiempo ───────────
# (patrones frecuentes en CAA que no estaban bien cubiertos: vocativo + pedido)

conceptos_mamá_papá_y_tiempo = [
    (["querer", "tomar", "agua", "mamá"], "Quiero tomar agua, mamá."),
    (["querer", "tomar", "agua", "papá"], "Quiero tomar agua, papá."),
    (["mamá", "querer", "comer"], "Mamá, quiero comer."),
    (["papá", "querer", "comer"], "Papá, quiero comer."),
    (["mamá", "querer", "abrazo"], "Mamá, quiero un abrazo."),
    (["papá", "querer", "jugar"], "Papá, quiero jugar."),
    (["mamá", "querer", "dormir"], "Mamá, quiero dormir."),
    (["papá", "querer", "agua"], "Papá, quiero agua."),
    (["mamá", "tener", "hambre"], "Mamá, tengo hambre."),
    (["papá", "tener", "sed"], "Papá, tengo sed."),
    (["mamá", "doler", "cabeza"], "Mamá, me duele la cabeza."),
    (["mamá", "querer", "salir"], "Mamá, quiero salir."),
    (["papá", "querer", "televisión"], "Papá, quiero ver la televisión."),
    (["mamá", "necesitar", "ayuda"], "Mamá, necesito ayuda."),
    (["papá", "necesitar", "ayuda"], "Papá, necesito ayuda."),
    (["mamá", "querer", "upa"], "Mamá, quiero upa."),
    (["papá", "tener", "miedo"], "Papá, tengo miedo."),
    (["mamá", "querer", "jugo"], "Mamá, quiero jugo."),
    (["triste", "hoy", "estar"], "Hoy estoy triste."),
    (["feliz", "hoy", "estar"], "Hoy estoy feliz."),
    (["cansado", "hoy", "estar"], "Hoy estoy cansado."),
    (["enojado", "ahora", "estar"], "Ahora estoy enojado."),
    (["nervioso", "hoy", "estar"], "Hoy estoy nervioso."),
    (["contento", "hoy", "estar"], "Hoy estoy contento."),
    (["aburrido", "ahora", "estar"], "Ahora estoy aburrido."),
    (["tranquilo", "hoy", "estar"], "Hoy estoy tranquilo."),
]

conceptos.extend(conceptos_mamá_papá_y_tiempo)

# ── 2c) Refuerzo de negaciones ──────────────────────────────────────────────
# La negación es crítica en CAA (invertir el significado es peor que un error
# de gramática), así que sumamos muchas variantes de "no + verbo + objeto"
# en distintas categorías para que el modelo no la "pierda" al generalizar.

conceptos_negacion = [
    (["no", "querer", "ir", "escuela"], "No quiero ir a la escuela."),
    (["no", "querer", "ir", "médico"], "No quiero ir al médico."),
    (["no", "querer", "ir", "baño"], "No quiero ir al baño."),
    (["no", "querer", "comer", "verdura"], "No quiero comer verdura."),
    (["no", "querer", "tomar", "medicina"], "No quiero tomar la medicina."),
    (["no", "querer", "jugar", "solo"], "No quiero jugar solo."),
    (["no", "querer", "ir", "casa", "amigo"], "No quiero ir a la casa de mi amigo."),
    (["no", "querer", "usar", "colectivo"], "No quiero usar el colectivo."),
    (["no", "querer", "hacer", "tarea"], "No quiero hacer la tarea."),
    (["no", "querer", "hablar", "nadie"], "No quiero hablar con nadie."),
    (["no", "querer", "salir", "hoy"], "No quiero salir hoy."),
    (["no", "querer", "sentarme", "adelante"], "No quiero sentarme adelante."),
    (["no", "necesitar", "ayuda"], "No necesito ayuda."),
    (["no", "tener", "hambre"], "No tengo hambre."),
    (["no", "tener", "sed"], "No tengo sed."),
    (["no", "tener", "miedo"], "No tengo miedo."),
    (["no", "estar", "bien"], "No estoy bien."),
    (["no", "estar", "triste"], "No estoy triste."),
    (["no", "poder", "caminar"], "No puedo caminar."),
    (["no", "poder", "dormir"], "No puedo dormir."),
    (["no", "querer", "ir", "escuela", "hoy"], "Hoy no quiero ir a la escuela."),
    (["no", "querer", "viajar", "auto"], "No quiero viajar en auto."),
    (["no", "querer", "ver", "amigo"], "No quiero ver a mi amigo."),
    (["amigo", "no", "querer", "compartir"], "Mi amigo no quiere compartir."),
    (["no", "querer", "bajar", "colectivo"], "No quiero bajar del colectivo."),
]

conceptos.extend(conceptos_negacion)

# ── 3) Generar permutaciones de cada concepto ───────────────────────────────────

pares_finales = []

for bag, frase in conceptos:
    perms = list(itertools.permutations(bag))
    if len(perms) > MAX_PERMS_POR_CONCEPTO:
        perms = random.sample(perms, MAX_PERMS_POR_CONCEPTO)
    vistos = set()
    for perm in perms:
        entrada = " ".join(perm)
        if entrada in vistos:
            continue
        vistos.add(entrada)
        pares_finales.append({"input": entrada, "output": frase})

random.shuffle(pares_finales)

print(f"Conceptos totales: {len(conceptos)}")
print(f"Pares generados (con permutaciones): {len(pares_finales)}")

with open("dataset_correccion.jsonl", "w", encoding="utf-8") as f:
    for par in pares_finales:
        f.write(json.dumps(par, ensure_ascii=False) + "\n")

print("Guardado en: dataset_correccion.jsonl")
