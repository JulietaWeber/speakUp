# SpeakUp — API de IA

Servicio FastAPI que usa el backend de SpeakUp para:

1. **Predecir** las próximas 3 palabras mientras el usuario arma una frase
   (`POST /predecir`).
2. **Personalizar** esa predicción con las frases de cada usuario
   (`POST /reentrenar`).
3. **Completar y corregir** la frase armada con pictogramas (`POST /corregir`):
   `["triste"]` → "Estoy triste.", sin perder nunca una palabra del usuario.

Los cuatro endpoints están entrenados y probados (`scripts/probar_endpoints.py`
pasa todos los chequeos obligatorios).

## Cómo correrla

```bash
cd IA
pip install -r requirements.txt    # fastapi, uvicorn, numpy, spacy + modelo es_core_news_md
uvicorn api:app --host 0.0.0.0 --port 8000
```
Arranca en ~10 s (carga de spaCy). En producción no hace falta torch.

## Archivos

```
IA/
├── api.py                    # endpoints FastAPI (uvicorn api:app)
├── funciones.py              # carga spaCy y los modelos una sola vez; une api.py con los modelos
├── prediccion.py             # /predecir y /reentrenar: n-gramas Kneser-Ney + historial por usuario
├── correccion.py             # /corregir: etiquetador de ediciones en numpy + corrección básica de respaldo
├── morfologia.py             # conjugación, género/número, tildes y plurales (reglas, nada aprendido)
├── modelo_prediccion.npz     # predicción: probabilidades por contexto (numpy)
├── modelo_prediccion.json    #   vocabulario y contextos
├── modelo_correccion.npz     # corrector: pesos de la red (numpy)
├── modelo_correccion.json    #   vocabularios, inserciones, umbrales y palabras fijas
├── lexico_correccion.json    #   género de sustantivos, tildes y verbos
├── requirements.txt          # dependencias de producción
├── Procfile                  # comando de arranque en el servidor
├── .gitignore
├── DOCUMENTACION.md
├── scripts/                  # entrenamiento y pruebas (no se usan en producción)
│   ├── corpus_caa.py             # genera datos/corpus_caa.txt
│   ├── dataset_completar.py      # genera datos/completar_frases.tsv
│   ├── descargar_tatoeba.py      # descarga datos/externos/ (opcional)
│   ├── entrenar_prediccion.py    # -> modelo_prediccion.*
│   ├── entrenar_correccion.py    # -> modelo_correccion.*, lexico_correccion.json
│   ├── probar_endpoints.py       # prueba de punta a punta de la API
│   ├── requirements-entrenamiento.txt   # lo de producción + torch y httpx
│   └── datos/
│       ├── corpus_caa.txt            # 47.995 frases correctas de CAA generadas
│       ├── frases_curadas.txt        # 2.602 frases escritas a mano
│       ├── completar_frases.tsv      # 115.853 pares pictogramas -> frase completa
│       ├── externos/                 # no versionado: spa_sentences.tsv.bz2 (descarga) y tatoeba_es.txt (filtrado)
│       └── cache/                    # no versionado: dataset_correccion.pkl (dataset del corrector ya procesado)
└── archivos_viejos/          # versiones anteriores, no se usan (tabla de abajo)
```

`modelos_usuarios/` (no versionada) se crea en ejecución con el historial de
cada usuario.

| `archivos_viejos/` | Qué era | Archivos |
|---|---|---|
| `prediccion_mlp/` | Predicción con un MLP de scikit-learn, sobreajustado a plantillas (`["quiero","tomar","un"]` → "nuevo" 90 %) | `modelo_final.py` (entrena), `dataset_predictivo.py` (pares), `modelo_base.pkl`, `encoder_salida.pkl`, `base_pares.pkl`; en `modelo_anterior/` la versión previa: `modelo_final.py`, `modelo_base.pkl`, `encoder_salida.pkl` |
| `correccion_seq2seq/` | Corrector seq2seq GRU: generaba la frase desde cero y salían frases incoherentes ("Quiero la agua, el fría y por el favor.") | `modelo_correccion.py` (entrena), `modelo_correccion.pt`, `dataset_correccion.jsonl` (20.266 pares) y los scripts que lo generaron: `dataset_correccion.py`, `frases_largas.py`, `gramatica.py`, `conjugacion.py` |
| `correccion_legacy/` | Primera versión del corrector | `modelo_correccion_legacy.py` (entrena), `modelo_correccion_legacy.pt`, `dataset_correccion_legacy.py` (genera el dataset) |

### Cómo se conectan

```
api.py ──> funciones.py ──> spaCy es_core_news_md (sin parser/NER)
                 ├──> prediccion.Predictor  (modelo_prediccion.*, modelos_usuarios/)
                 └──> correccion.Corrector  (modelo_correccion.*, lexico_correccion.json)
                      si faltan esos archivos -> correccion.correccion_basica

corpus_caa.py ──> corpus_caa.txt ───┬──> entrenar_prediccion.py ──> modelo_prediccion.*
frases_curadas.txt ─────────────────┤
descargar_tatoeba.py ──> externos/ ─┼──> entrenar_correccion.py ──> modelo_correccion.*, lexico_correccion.json
dataset_completar.py ──> completar_frases.tsv ┘
```
`morfologia.py` y las funciones de rasgos de `correccion.py` (`rasgos_doc`,
`ids_doc`, `doc_desde_palabras`) se usan igual al entrenar y en producción.

## Endpoints

**`GET /` y `GET /ping`** → `{"status": "ok"}`. `/ping` es para que
UptimeRobot mantenga despierto el servidor gratuito.

**`POST /predecir`** — `{"user_id": "001", "palabras": ["quiero", "ir", "al"]}`
- `palabras` (opcional, default `[]`): las últimas palabras del usuario. Se
  usan las últimas 3; con menos, se toma como principio de frase. Acepta
  mayúsculas, puntuación y elementos de varias palabras ("por favor").
- Devuelve **siempre** 3 palabras distintas, de mayor a menor probabilidad
  (porcentaje sobre todo el vocabulario, por eso no suman 100):
  `[{"palabra": "club", "probabilidad": 15.47}, ...]`. Menos de 1 ms de cómputo.

**`POST /reentrenar`** —
`{"user_id": "001", "datos": [{"categoria": "Casa", "frase": ["quiero", "ver", "televisión"]}]}`
- `categoria` se acepta pero no se usa. Devuelve
  `{"status": "ok", "pares_entrenados": N}` o `{"status": "sin_datos"}`.
- Acumulativo e instantáneo: suma conteos en `modelos_usuarios/<user_id>.json`
  (el `user_id` se sanea: no puede escribir fuera de la carpeta). Las palabras
  nuevas del usuario también se empiezan a sugerir.

**`POST /corregir`** — `{"palabras": ["mamá", "agua"]}` → `{"frase": "Mamá, quiero agua."}`.
Cada elemento es un pictograma y puede tener varias palabras ("tengo hambre").

| Entrada | Salida |
|---|---|
| `["triste"]` | `Estoy triste.` |
| `["pizza"]` | `Quiero pizza.` |
| `["tengo hambre", "pizza"]` | `Tengo hambre, quiero pizza.` |
| `["quiero", "ir", "parque", "con", "mi", "mamá"]` | `Quiero ir al parque con mi mamá.` |
| `["hola", "chau", "pizza", "triste"]` (sin sentido) | `Hola chau pizza triste.` |

- **Regla fundamental:** las palabras del usuario aparecen siempre, en su
  orden. Solo se agregan palabras; nunca se borra ni se reemplaza una. Lo
  único que puede cambiar es la forma de una palabra escrita a mano
  ("cansado" → "cansada", "mama" → "mamá"); las de los pictogramas y las de un
  elemento de varias palabras quedan tal cual.
- Si no se deduce nada útil vuelven las mismas palabras con mayúscula y punto
  (`["pelota"]` → `Pelota.`). Lista vacía → `""`. Con `?` o un interrogativo
  al principio → `¿...?`.

## Modelos

### Predicción (`prediccion.py`)
- 4-gramas con suavizado Kneser-Ney interpolado y un token `<s>` de inicio de
  frase. Un contexto nunca visto ("mañana vamos a") se predice por sus partes
  ("vamos a", "a").
- Palabra desconocida → la misma sin tildes ("mama" → "mamá") o la más
  parecida según los vectores de spaCy (coseno ≥ 0,55); si no hay, se usa el
  contexto que viene después.
- Personalización: se mezcla con el historial del usuario con peso
  `c / (c + 2)`, donde `c` = veces que el usuario usó ese contexto.
- Entrenamiento: `python scripts/entrenar_prediccion.py` sobre `corpus_caa.txt`
  y `frases_curadas.txt` (peso 3). Resultado: 2.479 palabras y 103.231
  contextos.

### Corrección (`correccion.py`)
- **Qué es:** una red BiGRU de 2 capas (1.493.205 parámetros) que, en vez de
  reescribir la frase, predice para cada palabra: qué insertar antes (118
  opciones cerradas: "el", "a la", "de", una coma, "quiero", "estoy", ",
  quiero", "porque"...), qué transformación aplicarle (género/número, persona
  del verbo, tilde) y si la frase es pregunta. Entradas por palabra:
  embedding, sufijo, vector de spaCy, POS/morfología y rasgos del léxico. Una
  sola pasada por frase (una segunda agregaba palabras de más).
- **Por qué no devuelve algo sin sentido ni pierde palabras:** no existen
  ediciones de borrar ni de reemplazar; solo se inserta texto de la lista
  cerrada o se usa otra forma de la misma palabra (`morfologia.py`). Las
  palabras de la app (`palabras_fijas`) no se transforman y no se inserta nada
  dentro de un elemento de varias palabras. Cada edición necesita alta
  confianza, hay un tope de ediciones y chequeos estructurales (no "la el", no
  terminar en preposición). Al final `conserva_palabras` vuelve a verificar la
  regla fundamental; si algo falla, se devuelve la frase del usuario con
  mayúscula y punto.
- **Entrenamiento:** `python scripts/entrenar_correccion.py --rehacer`
  (~1 h 10 min en CPU, necesita `scripts/requirements-entrenamiento.txt`). Sin
  `--rehacer` reusa `datos/cache/` y, si se cortó, sigue desde la última
  época. `--umbrales` recalcula solo los umbrales, `--solo-datos` muestra
  ejemplos sin entrenar y `--rapido` es una prueba de ~10 min que corrige
  bastante peor (no usarla para el modelo que se sube). Dos fuentes:
  1. **Frases correctas rotas a propósito** (corpus CAA, frases curadas y
     90.000 oraciones de [Tatoeba](https://tatoeba.org), CC BY 2.0 FR, que es
     opcional): falta un artículo, preposición, contracción, "que" o coma,
     género o número equivocado, verbo en otra persona que su sujeto
     explícito, falta una tilde. Como las roturas son nuestras, cada etiqueta
     se conoce exactamente. El corpus incluye ~3.000 frases complementarias
     (sujeto después del verbo: "hoy viene mi abuela"; "papas" la comida) que
     evitan correcciones malas ("viene a mi abuela", "papás").
  2. **Completar frases** (`completar_frases.tsv`): todas las secuencias de 1
     a 3 pictogramas de la app (más "mamá" y "papá"), las de 4 con sentido y
     la mitad de esa cantidad sin sentido (quedan iguales), más variantes con
     otras comidas, bebidas, actividades, estados y vocativos. Las de 1 y 2
     pictogramas se repiten ×30 y ×8.

  317.617 ejemplos de entrenamiento y 11.582 de validación nunca vistos, 12
  épocas en PyTorch, exportado a numpy.
- **Léxico:** género de los sustantivos, tildes y 1.109 verbos (también los
  que casi solo aparecen conjugados: "duele" → doler). `filtrar_verbos`
  descarta 44 verbos falsos, cuyas formas son casi siempre otras palabras
  ("pajar" → "paja", "piar" → "pie").
- **Umbrales y métricas** (validación: 5.999 frases del corpus y 5.583
  secuencias de 3-4 pictogramas, con la red numpy de producción). Se eligen
  los umbrales más bajos con ≥ 97 % de precisión en cada fuente por separado.

  | Edición | Umbral | Precisión corpus | Recall corpus | Precisión completar | Recall completar |
  |---|---|---|---|---|---|
  | Insertar | 0,95 | 98,1 % | 32,5 % | 99,6 % | 99,4 % |
  | Transformar | 0,90 | 97,3 % | 72,1 % | — | — |

  Quedan exactamente bien el 49,0 % de las frases del corpus (al resto le
  falta alguna corrección, casi nunca tiene una mal hecha) y el 98,8 % de las
  secuencias de pictogramas. Pregunta / exclamación: 97,4 % de acierto.

## Pruebas

```bash
cd IA
pip install -r scripts/requirements-entrenamiento.txt
python scripts/probar_endpoints.py     # sale con código 1 si falla algún chequeo obligatorio
```
Usa frases que no están en ningún dataset (lo verifica). Chequeos
obligatorios:
- `/predecir`: 54 contextos de 1 a 3 palabras, siempre 3 palabras, < 100 ms.
- `/reentrenar`: acumulativo, palabras nuevas, `user_id` malicioso.
- `/corregir`: 39 frases en < 2 s, sin inventar ni reordenar palabras de
  contenido y sin dejarlas peor armadas ("a la a la plaza").
- Completar: los 3 ejemplos de referencia exactos y, en un barrido de
  `completar_frases.tsv` (todas las secuencias de 1-2 pictogramas y 1.500 de
  3-4), la regla fundamental y < 2 s en cada una.

Último resultado: todo pasa.
- Corrección: 34/39 iguales a la esperada, ~14 ms por frase. Las otras 5 quedan
  sin corregir, no mal corregidas: "mi mamá está cansado", "una muñeca
  nuevo", "un vaso agua con hielo", "podés prender luz" y la coma de "quiero
  agua fría, por favor".
- Completar (4.238 secuencias, ~11 ms promedio, máx. 64 ms): el 98,3 % de las
  que tienen sentido sale igual que el dataset y el 99,9 % de las sin sentido
  queda igual.

## Limitaciones conocidas

- El corrector prefiere no corregir a corregir mal: en frases escritas a mano
  hace ~33 % de las inserciones y ~72 % de las transformaciones que harían
  falta. Bajar los umbrales en `modelo_correccion.json` corrige más pero con
  más errores.
- Completar solo arma lo que cubre la gramática de `dataset_completar.py`.
  Otras palabras se completan si la red las asocia a una categoría por su
  vector ("hamburguesa" → "Quiero hamburguesa."); si no, quedan iguales
  ("banana" → "Banana."). Un estado en la segunda parte ("pizza" + "triste")
  queda igual a propósito: enseñarlo hacía que la red agregara "porque estoy"
  delante de cualquier adjetivo ("Quiero agua porque estoy fría.").
- En secuencias de 4 pictogramas a veces falta una coma o una "y" ("Estaba
  feliz contento ayer."). Nunca se pierde una palabra.
- Un adjetivo lejos de su sustantivo ("mi mamá está cansado") y las palabras
  que existen con y sin tilde ("papas" / "papás", "esta" / "está") pueden
  quedar sin corregir si hay poco contexto.
