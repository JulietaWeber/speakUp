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
import os

random.seed(42)

MAX_PERMS_POR_CONCEPTO = 8

RUTA_DATASET_BASE = os.path.join("IA LLM", "dataset_caa.jsonl")
RUTA_DATASET_GENERADO = "dataset_correccion.jsonl"


def reconstruir_conceptos_desde_generado(ruta):
    """Reconstruye la lista de conceptos (bag de palabras -> frase correcta) a
    partir de un dataset_correccion.jsonl ya generado en una corrida anterior.

    Se usa como fallback cuando RUTA_DATASET_BASE (el dataset original de 300
    conceptos) no está disponible en el filesystem actual. Como cada concepto
    generó varias permutaciones del MISMO multiset de palabras, agrupar las
    filas por el multiset ordenado de "input" recupera el bag original sin
    pérdida de información: el orden no importa (es lo que el dataset le
    enseña a ignorar al modelo), así que cualquier permutación sirve para
    recuperar el bag."""
    vistos = {}
    orden = []
    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            par = json.loads(linea)
            bag = par["input"].split()
            clave = tuple(sorted(bag))
            if clave not in vistos:
                vistos[clave] = par["output"]
                orden.append(clave)
    return [(list(clave), vistos[clave]) for clave in orden]


# ── 1) Reusar el dataset ya armado (300 conceptos, 50 por categoría) ───────────

conceptos = []  # lista de (bag_de_palabras: list[str], frase_correcta: str)

if os.path.exists(RUTA_DATASET_BASE):
    with open(RUTA_DATASET_BASE, "r", encoding="utf-8") as f:
        for linea in f:
            par = json.loads(linea)
            bag = par["input"].split()
            conceptos.append((bag, par["output"]))
elif os.path.exists(RUTA_DATASET_GENERADO):
    print(
        f"AVISO: no se encontró '{RUTA_DATASET_BASE}', se reconstruyen los "
        f"conceptos base a partir de '{RUTA_DATASET_GENERADO}' (corrida anterior)."
    )
    conceptos.extend(reconstruir_conceptos_desde_generado(RUTA_DATASET_GENERADO))
else:
    print(
        f"AVISO: no se encontró ni '{RUTA_DATASET_BASE}' ni "
        f"'{RUTA_DATASET_GENERADO}'. Se arranca solo con los conceptos "
        f"definidos manualmente en este script."
    )

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

# ── 2d) Frases largas y complejas ────────────────────────────────────────────
# El modelo fallaba con frases largas porque el dataset original tenía sobre
# todo bags de 2-4 palabras. Estos conceptos usan bags de 5 a 9 palabras y
# frases de salida con oraciones compuestas (conectores, subordinadas,
# justificaciones, vocativos + razón), para que el encoder-decoder vea
# secuencias largas durante el entrenamiento y no solo en inferencia.

conceptos_frases_largas = [
    # Casa
    (["querer", "comer", "algo", "rico", "porque", "tener", "hambre"],
     "Quiero comer algo rico porque tengo mucha hambre."),
    (["necesitar", "ayuda", "ordenar", "cuarto", "antes", "dormir"],
     "Necesito ayuda para ordenar mi cuarto antes de dormir."),
    (["querer", "ver", "película", "papá", "mamá", "noche"],
     "Quiero ver una película con mamá y papá esta noche."),
    (["no", "querer", "bañarme", "ahora", "porque", "tener", "frío"],
     "No quiero bañarme ahora porque tengo frío."),
    (["querer", "invitar", "amigo", "casa", "jugar", "fin", "semana"],
     "Quiero invitar a un amigo a casa para jugar el fin de semana."),
    (["necesitar", "mamá", "ayudar", "hacer", "tarea", "difícil"],
     "Necesito que mamá me ayude a hacer una tarea difícil."),
    (["querer", "dormir", "temprano", "porque", "estar", "muy", "cansado"],
     "Quiero dormir temprano porque estoy muy cansado."),
    (["tener", "hambre", "sed", "querer", "comer", "tomar", "agua"],
     "Tengo hambre y sed, quiero comer y tomar agua."),
    (["no", "querer", "apagar", "televisión", "porque", "estar", "viendo", "programa"],
     "No quiero apagar la televisión porque estoy viendo un programa."),
    (["querer", "ayudar", "mamá", "cocinar", "cena", "hoy"],
     "Quiero ayudar a mamá a cocinar la cena hoy."),
    (["necesitar", "cambiarme", "ropa", "porque", "estar", "mojada", "sucia"],
     "Necesito cambiarme porque tengo la ropa mojada y sucia."),
    (["querer", "jugar", "afuera", "pero", "estar", "lloviendo", "mucho"],
     "Quiero jugar afuera pero está lloviendo mucho."),
    # Escuela
    (["no", "entender", "tarea", "matemática", "necesitar", "que", "maestra", "explicar"],
     "No entiendo la tarea de matemática, necesito que la maestra me la explique."),
    (["querer", "sentarme", "amigo", "lado", "porque", "trabajar", "mejor", "juntos"],
     "Quiero sentarme al lado de mi amigo porque trabajamos mejor juntos."),
    (["necesitar", "hoja", "carpeta", "lápiz", "porque", "olvidé", "cartuchera"],
     "Necesito una hoja, la carpeta y un lápiz porque olvidé la cartuchera."),
    (["querer", "presentar", "proyecto", "porque", "trabajar", "mucho", "él"],
     "Quiero presentar mi proyecto porque trabajé mucho en él."),
    (["no", "querer", "ir", "escuela", "hoy", "porque", "tener", "miedo", "prueba"],
     "No quiero ir a la escuela hoy porque tengo miedo a la prueba."),
    (["querer", "cambiar", "grupo", "porque", "compañero", "molestar", "siempre"],
     "Quiero cambiarme de grupo porque un compañero me molesta siempre."),
    (["necesitar", "ayuda", "terminar", "tarea", "antes", "recreo", "termine"],
     "Necesito ayuda para terminar la tarea antes de que termine el recreo."),
    (["querer", "ir", "excursión", "amigos", "pero", "necesitar", "permiso", "mamá"],
     "Quiero ir de excursión con mis amigos pero necesito el permiso de mamá."),
    (["olvidé", "cuaderno", "casa", "necesitar", "hoja", "prestada"],
     "Olvidé el cuaderno en casa, necesito que me presten una hoja."),
    (["querer", "participar", "clase", "pero", "tener", "vergüenza", "hablar"],
     "Quiero participar en clase pero tengo vergüenza de hablar."),
    # Médico
    (["doler", "cabeza", "mucho", "desde", "mañana", "querer", "tomar", "algo"],
     "Me duele mucho la cabeza desde la mañana, quiero tomar algo."),
    (["tener", "fiebre", "alta", "necesitar", "que", "doctora", "revisar", "ahora"],
     "Tengo fiebre alta, necesito que la doctora me revise ahora."),
    (["querer", "saber", "resultado", "análisis", "porque", "estar", "preocupado"],
     "Quiero saber el resultado del análisis porque estoy preocupado."),
    (["necesitar", "curita", "rodilla", "porque", "caer", "jugando", "afuera"],
     "Necesito una curita en la rodilla porque me caí jugando afuera."),
    (["no", "querer", "tomar", "medicina", "porque", "tener", "sabor", "feo"],
     "No quiero tomar la medicina porque tiene un sabor feo."),
    (["tener", "tos", "fuerte", "no", "parar", "desde", "noche", "anterior"],
     "Tengo una tos fuerte que no para desde la noche anterior."),
    (["querer", "mamá", "quedarse", "conmigo", "porque", "tener", "miedo", "inyección"],
     "Quiero que mamá se quede conmigo porque tengo miedo a la inyección."),
    (["necesitar", "reposo", "casa", "porque", "doctor", "decir", "descansar"],
     "Necesito hacer reposo en casa porque el doctor dijo que descanse."),
    (["doler", "estómago", "después", "comer", "querer", "acostarme", "un", "rato"],
     "Me duele el estómago después de comer, quiero acostarme un rato."),
    # Emociones
    (["estar", "triste", "hoy", "porque", "pelear", "mejor", "amigo"],
     "Hoy estoy triste porque peleé con mi mejor amigo."),
    (["estar", "feliz", "mucho", "porque", "mañana", "ir", "cumpleaños", "primo"],
     "Estoy muy feliz porque mañana voy al cumpleaños de mi primo."),
    (["sentir", "nervioso", "porque", "tener", "prueba", "importante", "mañana"],
     "Me siento nervioso porque tengo una prueba importante mañana."),
    (["estar", "enojado", "porque", "hermano", "romper", "juguete", "favorito"],
     "Estoy enojado porque mi hermano rompió mi juguete favorito."),
    (["necesitar", "hablar", "alguien", "porque", "sentirme", "solo", "últimamente"],
     "Necesito hablar con alguien porque me siento solo últimamente."),
    (["estar", "orgulloso", "mí", "mismo", "porque", "terminar", "algo", "difícil"],
     "Estoy orgulloso de mí mismo porque terminé algo difícil."),
    (["sentir", "vergüenza", "porque", "equivocarme", "frente", "todos"],
     "Siento vergüenza porque me equivoqué frente a todos."),
    (["no", "saber", "qué", "sentir", "porque", "ser", "día", "raro"],
     "No sé qué estoy sintiendo porque fue un día raro."),
    (["estar", "asustado", "porque", "escuchar", "ruido", "fuerte", "afuera"],
     "Estoy asustado porque escuché un ruido fuerte afuera."),
    # Transporte
    (["querer", "bajar", "próxima", "parada", "porque", "llegar", "tarde", "escuela"],
     "Quiero bajar en la próxima parada porque voy a llegar tarde a la escuela."),
    (["perder", "colectivo", "necesitar", "ayuda", "saber", "cuándo", "viene", "otro"],
     "Perdí el colectivo, necesito ayuda para saber cuándo viene otro."),
    (["estar", "mareado", "colectivo", "necesitar", "aire", "ventanilla", "abierta"],
     "Estoy mareado en el colectivo, necesito que abran la ventanilla."),
    (["necesitar", "ayuda", "subir", "escalón", "porque", "doler", "pierna"],
     "Necesito ayuda para subir el escalón porque me duele la pierna."),
    (["querer", "ir", "casa", "auto", "porque", "estar", "lloviendo", "mucho"],
     "Quiero ir a casa en auto porque está lloviendo mucho."),
    (["falta", "mucho", "llegar", "porque", "estar", "cansado", "viaje", "largo"],
     "¿Falta mucho para llegar? Estoy cansado, el viaje es largo."),
    (["necesitar", "chofer", "esperar", "porque", "bajar", "silla", "ruedas"],
     "Necesito que el chofer me espere porque bajo con la silla de ruedas."),
    (["querer", "sentarme", "ventana", "colectivo", "porque", "gustar", "ver", "afuera"],
     "Quiero sentarme junto a la ventana porque me gusta ver hacia afuera."),
    # Amigos
    (["querer", "pedir", "perdón", "amigo", "porque", "decir", "algo", "feo"],
     "Quiero pedirle perdón a mi amigo porque le dije algo feo."),
    (["amigo", "no", "querer", "jugar", "conmigo", "no", "saber", "por", "qué"],
     "Mi amigo no quiere jugar conmigo y no sé por qué."),
    (["querer", "invitar", "amigos", "casa", "jugar", "videojuegos", "sábado"],
     "Quiero invitar a mis amigos a casa para jugar videojuegos el sábado."),
    (["extrañar", "amigo", "vivir", "otra", "ciudad", "querer", "llamarlo"],
     "Extraño a mi amigo que vive en otra ciudad, quiero llamarlo."),
    (["querer", "hacer", "las", "paces", "amigo", "porque", "extrañar", "jugar", "juntos"],
     "Quiero hacer las paces con mi amigo porque extraño jugar juntos."),
    (["amigo", "contarme", "secreto", "no", "querer", "contarlo", "nadie"],
     "Mi amigo me contó un secreto y no quiero contárselo a nadie."),
    (["querer", "presentar", "amigo", "nuevo", "otros", "amigos", "escuela"],
     "Quiero presentarle mi amigo nuevo a los otros amigos de la escuela."),
    (["amigo", "ayudarme", "tarea", "querer", "agradecerle", "algo", "especial"],
     "Mi amigo me ayudó con la tarea, quiero agradecerle con algo especial."),
]

conceptos.extend(conceptos_frases_largas)

# ── 2e) Deduplicar por bag ───────────────────────────────────────────────────
# Cuando se reconstruye desde RUTA_DATASET_GENERADO (fallback del punto 1),
# ese archivo ya incluye los bloques manuales de arriba (fueron parte de la
# corrida anterior), así que sin este paso quedarían contados dos veces.

_vistos_bag = set()
_conceptos_dedup = []
for bag, frase in conceptos:
    clave = tuple(sorted(bag))
    if clave in _vistos_bag:
        continue
    _vistos_bag.add(clave)
    _conceptos_dedup.append((bag, frase))
conceptos = _conceptos_dedup

# ── 3) Generar permutaciones de cada concepto ───────────────────────────────────
# Se generan permutaciones al azar (en vez de materializar TODAS las
# permutaciones con itertools, que para bags largos de 8-9 palabras sería
# carísimo: 9! = 362880) hasta juntar MAX_PERMS_POR_CONCEPTO distintas o
# agotar los intentos razonables, lo que además escala bien sin importar el
# largo del bag.

def generar_permutaciones(bag, k):
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


pares_finales = []

for bag, frase in conceptos:
    perms = generar_permutaciones(bag, MAX_PERMS_POR_CONCEPTO)
    for perm in perms:
        entrada = " ".join(perm)
        pares_finales.append({"input": entrada, "output": frase})

random.shuffle(pares_finales)

print(f"Conceptos totales: {len(conceptos)}")
print(f"Pares generados (con permutaciones): {len(pares_finales)}")

with open("dataset_correccion.jsonl", "w", encoding="utf-8") as f:
    for par in pares_finales:
        f.write(json.dumps(par, ensure_ascii=False) + "\n")

print("Guardado en: dataset_correccion.jsonl")
