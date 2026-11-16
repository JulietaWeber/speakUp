"""
Script de prueba del modelo corrector BiGRU
============================================
Evalúa el corrector con un dataset armado a mano (nunca visto durante el
entrenamiento) y reporta dos métricas:

  - Exacta:            % de frases donde la salida coincide exactamente
                       con la frase esperada (mayúsculas y puntuación incluidas)
  - Palabras correctas: % de palabras de la frase esperada que aparecen
                        en la salida del corrector

Uso (desde el root del proyecto speakUp/):
    python IA/scripts/pruebas/probar_correccion.py

Requiere spaCy y el modelo cargado:
    pip install spacy
    python -m spacy download es_core_news_md
"""

import os
import sys

# ── Rutas (relativas al root del proyecto) ────────────────────────────────────
AQUI  = os.path.dirname(os.path.abspath(__file__))   # IA/scripts/pruebas/
IA    = os.path.dirname(os.path.dirname(AQUI))        # IA/
RAIZ  = os.path.dirname(IA)                           # speakUp/

# Para importar correccion.py y morfologia.py que están en IA/
sys.path.insert(0, IA)

RUTA_PESOS  = os.path.join(IA, "modelo_correccion.npz")
RUTA_CONFIG = os.path.join(IA, "modelo_correccion.json")
RUTA_LEXICO = os.path.join(IA, "lexico_correccion.json")

# ── Dataset de prueba ─────────────────────────────────────────────────────────
# Formato: {"entrada": [palabras del usuario], "correcta": "Frase esperada."}
# Ninguna de estas frases se usó para entrenar el modelo.
# La métrica "exacta" compara la salida con "correcta" carácter por carácter.
# La métrica "palabras correctas" mide cuántas palabras de "correcta" aparecen
# en la salida (sin importar el orden exacto).

DATASET = [
    # ── Inserción de artículos ──
    {"entrada": ["quiero", "agua"],              "correcta": "Quiero agua."},
    {"entrada": ["quiero", "leche"],             "correcta": "Quiero leche."},
    {"entrada": ["quiero", "jugo"],              "correcta": "Quiero jugo."},
    {"entrada": ["quiero", "pan"],               "correcta": "Quiero pan."},
    {"entrada": ["quiero", "pizza"],             "correcta": "Quiero pizza."},
    {"entrada": ["quiero", "helado"],            "correcta": "Quiero helado."},
    {"entrada": ["quiero", "galletitas"],        "correcta": "Quiero galletitas."},
    {"entrada": ["quiero", "manzana"],           "correcta": "Quiero manzana."},
    {"entrada": ["quiero", "banana"],            "correcta": "Quiero banana."},
    {"entrada": ["quiero", "yogur"],             "correcta": "Quiero yogur."},

    # ── Completar frases con sujeto ──
    {"entrada": ["yo", "agua"],                  "correcta": "Yo quiero agua."},
    {"entrada": ["yo", "comer"],                 "correcta": "Yo quiero comer."},
    {"entrada": ["yo", "dormir"],                "correcta": "Yo quiero dormir."},
    {"entrada": ["yo", "jugar"],                 "correcta": "Yo quiero jugar."},
    {"entrada": ["yo", "ir"],                    "correcta": "Yo quiero ir."},
    {"entrada": ["mamá", "agua"],                "correcta": "Mamá, quiero agua."},
    {"entrada": ["papá", "agua"],                "correcta": "Papá, quiero agua."},
    {"entrada": ["mamá", "comer"],               "correcta": "Mamá, quiero comer."},
    {"entrada": ["papá", "jugar"],               "correcta": "Papá, quiero jugar."},
    {"entrada": ["mamá", "ir", "parque"],        "correcta": "Mamá, quiero ir al parque."},

    # ── Inserción de preposiciones ──
    {"entrada": ["quiero", "ir", "baño"],        "correcta": "Quiero ir al baño."},
    {"entrada": ["quiero", "ir", "parque"],      "correcta": "Quiero ir al parque."},
    {"entrada": ["quiero", "ir", "casa"],        "correcta": "Quiero ir a casa."},
    {"entrada": ["quiero", "ir", "escuela"],     "correcta": "Quiero ir a la escuela."},
    {"entrada": ["voy", "parque"],               "correcta": "Voy al parque."},
    {"entrada": ["voy", "baño"],                 "correcta": "Voy al baño."},
    {"entrada": ["voy", "casa"],                 "correcta": "Voy a casa."},
    {"entrada": ["estoy", "casa"],               "correcta": "Estoy en casa."},
    {"entrada": ["estoy", "escuela"],            "correcta": "Estoy en la escuela."},
    {"entrada": ["estoy", "parque"],             "correcta": "Estoy en el parque."},

    # ── Estados y emociones ──
    {"entrada": ["estoy", "bien"],               "correcta": "Estoy bien."},
    {"entrada": ["estoy", "mal"],                "correcta": "Estoy mal."},
    {"entrada": ["estoy", "triste"],             "correcta": "Estoy triste."},
    {"entrada": ["estoy", "contento"],           "correcta": "Estoy contento."},
    {"entrada": ["estoy", "cansado"],            "correcta": "Estoy cansado."},
    {"entrada": ["estoy", "enojado"],            "correcta": "Estoy enojado."},
    {"entrada": ["estoy", "asustado"],           "correcta": "Estoy asustado."},
    {"entrada": ["estoy", "aburrido"],           "correcta": "Estoy aburrido."},
    {"entrada": ["tengo", "miedo"],              "correcta": "Tengo miedo."},
    {"entrada": ["tengo", "sueño"],              "correcta": "Tengo sueño."},

    # ── Dolor y salud ──
    {"entrada": ["me", "duele", "cabeza"],       "correcta": "Me duele la cabeza."},
    {"entrada": ["me", "duele", "panza"],        "correcta": "Me duele la panza."},
    {"entrada": ["me", "duele", "garganta"],     "correcta": "Me duele la garganta."},
    {"entrada": ["me", "duele", "espalda"],      "correcta": "Me duele la espalda."},
    {"entrada": ["me", "duele", "brazo"],        "correcta": "Me duele el brazo."},
    {"entrada": ["me", "duele", "pie"],          "correcta": "Me duele el pie."},
    {"entrada": ["tengo", "fiebre"],             "correcta": "Tengo fiebre."},
    {"entrada": ["tengo", "tos"],                "correcta": "Tengo tos."},
    {"entrada": ["tengo", "hambre"],             "correcta": "Tengo hambre."},
    {"entrada": ["tengo", "sed"],                "correcta": "Tengo sed."},

    # ── Necesidades ──
    {"entrada": ["quiero", "dormir"],            "correcta": "Quiero dormir."},
    {"entrada": ["quiero", "descansar"],         "correcta": "Quiero descansar."},
    {"entrada": ["quiero", "bañarme"],           "correcta": "Quiero bañarme."},
    {"entrada": ["quiero", "cambiarme"],         "correcta": "Quiero cambiarme."},
    {"entrada": ["quiero", "lavarme", "dientes"],"correcta": "Quiero lavarme los dientes."},
    {"entrada": ["quiero", "salir"],             "correcta": "Quiero salir."},
    {"entrada": ["quiero", "quedarme"],          "correcta": "Quiero quedarme."},
    {"entrada": ["quiero", "jugar"],             "correcta": "Quiero jugar."},
    {"entrada": ["quiero", "mirar", "tv"],       "correcta": "Quiero mirar tv."},
    {"entrada": ["quiero", "escuchar", "música"],"correcta": "Quiero escuchar música."},

    # ── Con mamá / papá / familia ──
    {"entrada": ["quiero", "mamá"],              "correcta": "Quiero a mamá."},
    {"entrada": ["quiero", "papá"],              "correcta": "Quiero a papá."},
    {"entrada": ["llamar", "mamá"],              "correcta": "Quiero llamar a mamá."},
    {"entrada": ["llamar", "papá"],              "correcta": "Quiero llamar a papá."},
    {"entrada": ["ir", "mamá"],                  "correcta": "Quiero ir con mamá."},
    {"entrada": ["ir", "papá"],                  "correcta": "Quiero ir con papá."},
    {"entrada": ["mi", "mamá", "agua"],          "correcta": "Mi mamá quiere agua."},
    {"entrada": ["mi", "papá", "dormir"],        "correcta": "Mi papá quiere dormir."},
    {"entrada": ["mi", "hermano", "jugar"],      "correcta": "Mi hermano quiere jugar."},
    {"entrada": ["mi", "abuela", "comer"],       "correcta": "Mi abuela quiere comer."},

    # ── Frases con dos palabras del usuario ──
    {"entrada": ["quiero", "comer", "pizza"],    "correcta": "Quiero comer pizza."},
    {"entrada": ["quiero", "comer", "pasta"],    "correcta": "Quiero comer pasta."},
    {"entrada": ["quiero", "comer", "arroz"],    "correcta": "Quiero comer arroz."},
    {"entrada": ["quiero", "tomar", "agua"],     "correcta": "Quiero tomar agua."},
    {"entrada": ["quiero", "tomar", "leche"],    "correcta": "Quiero tomar leche."},
    {"entrada": ["quiero", "tomar", "jugo"],     "correcta": "Quiero tomar jugo."},
    {"entrada": ["quiero", "ver", "tv"],         "correcta": "Quiero ver tv."},
    {"entrada": ["quiero", "andar", "bici"],     "correcta": "Quiero andar en bici."},
    {"entrada": ["quiero", "ir", "médico"],      "correcta": "Quiero ir al médico."},
    {"entrada": ["quiero", "ir", "colegio"],     "correcta": "Quiero ir al colegio."},

    # ── Corrección de persona verbal ──
    {"entrada": ["yo", "tengo", "hambre"],       "correcta": "Yo tengo hambre."},
    {"entrada": ["yo", "tengo", "sed"],          "correcta": "Yo tengo sed."},
    {"entrada": ["yo", "quiero", "agua"],        "correcta": "Yo quiero agua."},
    {"entrada": ["yo", "quiero", "dormir"],      "correcta": "Yo quiero dormir."},
    {"entrada": ["yo", "estoy", "bien"],         "correcta": "Yo estoy bien."},
    {"entrada": ["yo", "estoy", "mal"],          "correcta": "Yo estoy mal."},
    {"entrada": ["yo", "voy", "parque"],         "correcta": "Yo voy al parque."},
    {"entrada": ["yo", "voy", "casa"],           "correcta": "Yo voy a casa."},
    {"entrada": ["yo", "me", "duele", "cabeza"], "correcta": "Yo me duele la cabeza."},
    {"entrada": ["yo", "necesito", "ayuda"],     "correcta": "Yo necesito ayuda."},

    # ── Frases con lugar ──
    {"entrada": ["voy", "médico"],               "correcta": "Voy al médico."},
    {"entrada": ["voy", "colegio"],              "correcta": "Voy al colegio."},
    {"entrada": ["voy", "plaza"],                "correcta": "Voy a la plaza."},
    {"entrada": ["voy", "pileta"],               "correcta": "Voy a la pileta."},
    {"entrada": ["voy", "cocina"],               "correcta": "Voy a la cocina."},
    {"entrada": ["estoy", "cocina"],             "correcta": "Estoy en la cocina."},
    {"entrada": ["estoy", "baño"],               "correcta": "Estoy en el baño."},
    {"entrada": ["estoy", "cama"],               "correcta": "Estoy en la cama."},
    {"entrada": ["estoy", "sillón"],             "correcta": "Estoy en el sillón."},
    {"entrada": ["estoy", "jardín"],             "correcta": "Estoy en el jardín."},

    # ── Pedidos y permisos ──
    {"entrada": ["quiero", "prender", "tele"],   "correcta": "Quiero prender la tele."},
    {"entrada": ["quiero", "apagar", "tele"],    "correcta": "Quiero apagar la tele."},
    {"entrada": ["quiero", "abrir", "ventana"],  "correcta": "Quiero abrir la ventana."},
    {"entrada": ["quiero", "cerrar", "puerta"],  "correcta": "Quiero cerrar la puerta."},
    {"entrada": ["quiero", "poner", "música"],   "correcta": "Quiero poner la música."},
    {"entrada": ["quiero", "buscar", "mochila"], "correcta": "Quiero buscar mi mochila."},
    {"entrada": ["perdí", "mochila"],            "correcta": "Perdí la mochila."},
    {"entrada": ["no", "encuentro", "mochila"],  "correcta": "No encuentro la mochila."},
    {"entrada": ["dame", "agua"],                "correcta": "Dame agua."},
    {"entrada": ["dame", "leche"],               "correcta": "Dame leche."},

    # ── Negaciones ──
    {"entrada": ["no", "quiero"],                "correcta": "No quiero."},
    {"entrada": ["no", "quiero", "agua"],        "correcta": "No quiero agua."},
    {"entrada": ["no", "quiero", "comer"],       "correcta": "No quiero comer."},
    {"entrada": ["no", "quiero", "ir"],          "correcta": "No quiero ir."},
    {"entrada": ["no", "quiero", "dormir"],      "correcta": "No quiero dormir."},
    {"entrada": ["no", "tengo", "hambre"],       "correcta": "No tengo hambre."},
    {"entrada": ["no", "tengo", "sed"],          "correcta": "No tengo sed."},
    {"entrada": ["no", "me", "gusta"],           "correcta": "No me gusta."},
    {"entrada": ["no", "puedo"],                 "correcta": "No puedo."},
    {"entrada": ["no", "sé"],                    "correcta": "No sé."},

    # ── Frases con conector ──
    {"entrada": ["quiero", "agua", "y", "leche"],        "correcta": "Quiero agua y leche."},
    {"entrada": ["quiero", "pizza", "y", "jugo"],        "correcta": "Quiero pizza y jugo."},
    {"entrada": ["tengo", "hambre", "y", "sed"],         "correcta": "Tengo hambre y sed."},
    {"entrada": ["estoy", "cansado", "y", "triste"],     "correcta": "Estoy cansado y triste."},
    {"entrada": ["quiero", "comer", "y", "dormir"],      "correcta": "Quiero comer y dormir."},
    {"entrada": ["quiero", "jugar", "y", "mirar", "tv"], "correcta": "Quiero jugar y mirar tv."},
    {"entrada": ["voy", "parque", "y", "juego"],         "correcta": "Voy al parque y juego."},
    {"entrada": ["tengo", "frío", "y", "sueño"],         "correcta": "Tengo frío y sueño."},
    {"entrada": ["me", "duele", "cabeza", "y", "panza"], "correcta": "Me duele la cabeza y la panza."},
    {"entrada": ["quiero", "agua", "porque", "sed"],     "correcta": "Quiero agua porque tengo sed."},

    # ── Frases más largas / complejas ──
    {"entrada": ["mamá", "quiero", "ir", "parque"],      "correcta": "Mamá, quiero ir al parque."},
    {"entrada": ["papá", "quiero", "comer", "pizza"],    "correcta": "Papá, quiero comer pizza."},
    {"entrada": ["mamá", "me", "duele", "cabeza"],       "correcta": "Mamá, me duele la cabeza."},
    {"entrada": ["papá", "tengo", "hambre"],             "correcta": "Papá, tengo hambre."},
    {"entrada": ["mamá", "estoy", "triste"],             "correcta": "Mamá, estoy triste."},
    {"entrada": ["hoy", "quiero", "ir", "parque"],       "correcta": "Hoy quiero ir al parque."},
    {"entrada": ["mañana", "voy", "médico"],             "correcta": "Mañana voy al médico."},
    {"entrada": ["hoy", "tengo", "hambre"],              "correcta": "Hoy tengo hambre."},
    {"entrada": ["mañana", "quiero", "comer", "pizza"],  "correcta": "Mañana quiero comer pizza."},
    {"entrada": ["hoy", "estoy", "bien"],                "correcta": "Hoy estoy bien."},

    # ── Frases de un pictograma ──
    {"entrada": ["hola"],                        "correcta": "Hola."},
    {"entrada": ["gracias"],                     "correcta": "Gracias."},
    {"entrada": ["perdón"],                      "correcta": "Perdón."},
    {"entrada": ["ayuda"],                       "correcta": "Ayuda."},
    {"entrada": ["bien"],                        "correcta": "Bien."},
    {"entrada": ["mal"],                         "correcta": "Mal."},
    {"entrada": ["sí"],                          "correcta": "Sí."},
    {"entrada": ["no"],                          "correcta": "No."},
    {"entrada": ["agua"],                        "correcta": "Agua."},
    {"entrada": ["comer"],                       "correcta": "Comer."},

    # ── Más rutinas ──
    {"entrada": ["quiero", "desayunar"],         "correcta": "Quiero desayunar."},
    {"entrada": ["quiero", "almorzar"],          "correcta": "Quiero almorzar."},
    {"entrada": ["quiero", "merendar"],          "correcta": "Quiero merendar."},
    {"entrada": ["quiero", "cenar"],             "correcta": "Quiero cenar."},
    {"entrada": ["quiero", "estudiar"],          "correcta": "Quiero estudiar."},
    {"entrada": ["tengo", "tarea"],              "correcta": "Tengo tarea."},
    {"entrada": ["quiero", "leer"],              "correcta": "Quiero leer."},
    {"entrada": ["quiero", "dibujar"],           "correcta": "Quiero dibujar."},
    {"entrada": ["quiero", "pintar"],            "correcta": "Quiero pintar."},
    {"entrada": ["quiero", "correr"],            "correcta": "Quiero correr."},

    # ── Clima y contexto ──
    {"entrada": ["hace", "frío"],                "correcta": "Hace frío."},
    {"entrada": ["hace", "calor"],               "correcta": "Hace calor."},
    {"entrada": ["hay", "sol"],                  "correcta": "Hay sol."},
    {"entrada": ["está", "lloviendo"],           "correcta": "Está lloviendo."},
    {"entrada": ["tengo", "frío"],               "correcta": "Tengo frío."},
    {"entrada": ["tengo", "calor"],              "correcta": "Tengo calor."},
    {"entrada": ["quiero", "abrigo"],            "correcta": "Quiero el abrigo."},
    {"entrada": ["quiero", "paraguas"],          "correcta": "Quiero el paraguas."},
    {"entrada": ["afuera", "frío"],              "correcta": "Afuera hace frío."},
    {"entrada": ["afuera", "sol"],               "correcta": "Afuera hay sol."},

    # ── Pedir ayuda / comunicar ──
    {"entrada": ["necesito", "ayuda"],           "correcta": "Necesito ayuda."},
    {"entrada": ["quiero", "hablar"],            "correcta": "Quiero hablar."},
    {"entrada": ["quiero", "hablar", "mamá"],    "correcta": "Quiero hablar con mamá."},
    {"entrada": ["quiero", "hablar", "papá"],    "correcta": "Quiero hablar con papá."},
    {"entrada": ["no", "entiendo"],              "correcta": "No entiendo."},
    {"entrada": ["puedo", "ir", "baño"],         "correcta": "¿Puedo ir al baño?"},
    {"entrada": ["puedo", "comer"],              "correcta": "¿Puedo comer?"},
    {"entrada": ["puedo", "jugar"],              "correcta": "¿Puedo jugar?"},
    {"entrada": ["puedo", "salir"],              "correcta": "¿Puedo salir?"},
    {"entrada": ["cuándo", "comemos"],           "correcta": "¿Cuándo comemos?"},

    # ── Más frases con ropa / objetos ──
    {"entrada": ["quiero", "mochila"],           "correcta": "Quiero la mochila."},
    {"entrada": ["quiero", "libro"],             "correcta": "Quiero el libro."},
    {"entrada": ["quiero", "juguete"],           "correcta": "Quiero el juguete."},
    {"entrada": ["quiero", "pelota"],            "correcta": "Quiero la pelota."},
    {"entrada": ["quiero", "remera"],            "correcta": "Quiero la remera."},
    {"entrada": ["quiero", "campera"],           "correcta": "Quiero la campera."},
    {"entrada": ["quiero", "gorra"],             "correcta": "Quiero la gorra."},
    {"entrada": ["quiero", "zapatillas"],        "correcta": "Quiero las zapatillas."},
    {"entrada": ["quiero", "medias"],            "correcta": "Quiero las medias."},
    {"entrada": ["quiero", "pantalón"],          "correcta": "Quiero el pantalón."},
]


# ── Métricas ──────────────────────────────────────────────────────────────────

def palabras_correctas(salida, esperada):
    """% de palabras de la frase esperada que aparecen en la salida
    (comparación en minúsculas, sin puntuación)."""
    import re
    limpiar = lambda s: re.findall(r"[a-záéíóúüñ]+", s.lower())
    palabras_esp = limpiar(esperada)
    palabras_sal = set(limpiar(salida))
    if not palabras_esp:
        return 1.0
    coincidencias = sum(1 for p in palabras_esp if p in palabras_sal)
    return coincidencias / len(palabras_esp)


def evaluar():
    print("Cargando modelo corrector...")
    try:
        import spacy
        nlp = spacy.load("es_core_news_md")
    except Exception as e:
        print(f"ERROR: No se pudo cargar spaCy: {e}")
        print("Instalar con: pip install spacy && python -m spacy download es_core_news_md")
        sys.exit(1)

    try:
        from correccion import Corrector
        corrector = Corrector(nlp, RUTA_PESOS, RUTA_CONFIG, RUTA_LEXICO)
    except Exception as e:
        print(f"ERROR: No se pudo cargar el corrector: {e}")
        sys.exit(1)

    print(f"Modelo cargado. Evaluando {len(DATASET)} casos...\n")

    ancho_entrada  = 35
    ancho_salida   = 45
    ancho_esperada = 45

    encabezado = f"{'ENTRADA':<{ancho_entrada}} {'SALIDA':<{ancho_salida}} {'ESPERADA':<{ancho_esperada}} EX   PAL%"
    print("=" * len(encabezado))
    print(encabezado)
    print("=" * len(encabezado))

    total_exactas   = 0
    total_palabras  = 0.0
    resultados      = []

    for caso in DATASET:
        entrada  = caso["entrada"]
        esperada = caso["correcta"]
        try:
            salida = corrector.corregir(entrada)
        except Exception as e:
            salida = f"[ERROR: {e}]"

        exacta  = salida.strip() == esperada.strip()
        pct_pal = palabras_correctas(salida, esperada)

        total_exactas  += int(exacta)
        total_palabras += pct_pal
        resultados.append((entrada, salida, esperada, exacta, pct_pal))

        entrada_str  = " ".join(entrada)
        marca_ex     = "✓" if exacta else "✗"
        print(f"{entrada_str:<{ancho_entrada}} {salida:<{ancho_salida}} {esperada:<{ancho_esperada}} {marca_ex}  {pct_pal*100:5.1f}%")

    n = len(DATASET)
    pct_exactas  = total_exactas  / n * 100
    pct_palabras = total_palabras / n * 100

    print("=" * len(encabezado))
    print(f"\nResultados sobre {n} casos:")
    print(f"  Exacta            : {total_exactas}/{n} = {pct_exactas:.1f}%")
    print(f"  Palabras correctas: {pct_palabras:.1f}%")

    # Desglose por longitud de entrada
    print("\n── Desglose por longitud de entrada ──")
    for largo in sorted(set(len(c["entrada"]) for c in DATASET)):
        grupo = [(s, e, ex, pp) for (en, s, e, ex, pp) in resultados if len(en) == largo]
        ex_g  = sum(r[2] for r in grupo)
        pal_g = sum(r[3] for r in grupo) / len(grupo) * 100
        print(f"  {largo} palabra(s): {ex_g}/{len(grupo)} exactas = {ex_g/len(grupo)*100:.1f}%  |  palabras {pal_g:.1f}%")

    # Casos fallidos
    fallidos = [(en, s, e) for (en, s, e, ex, _) in resultados if not ex]
    if fallidos:
        print(f"\n── Casos no exactos ({len(fallidos)}) ──")
        for en, s, e in fallidos[:20]:
            print(f"  [{' '.join(en)}]  →  {s!r}  (esperado: {e!r})")
        if len(fallidos) > 20:
            print(f"  ... y {len(fallidos) - 20} más")


if __name__ == "__main__":
    evaluar()
