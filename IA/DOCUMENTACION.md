# SpeakUp — API de IA

Documentación para code review. `IA/` es un servicio FastAPI que el backend
de SpeakUp usa para:

1. **Predecir** las próximas 3 palabras mientras el usuario arma una frase en
   el tablero de CAA (`POST /predecir`).
2. **Personalizar** esa predicción con las frases de cada usuario
   (`POST /reentrenar`).
3. **Corregir** la frase armada con correcciones mínimas (`POST /corregir`).

> **Estado (al hacer este commit):** `/predecir`, `/reentrenar`, `/` y `/ping`
> están terminados y probados. El modelo nuevo de `/corregir` (etiquetador de
> ediciones) está implementado en `correccion.py` pero **sus pesos todavía no
> están en el repo** (el entrenamiento estaba en curso). Mientras falten
> `modelo_correccion.npz`, `modelo_correccion.json` y `lexico_correccion.json`,
> la API arranca igual y `/corregir` usa la **corrección básica**: devuelve las
> palabras del usuario, en su orden, con contracciones ("a el" → "al"),
> mayúscula inicial y puntuación final. Nunca inventa ni reordena palabras.
> Ver [Pendientes](#pendientes).

---

## Cómo correrla

```bash
cd IA
pip install -r requirements.txt          # producción: fastapi, uvicorn, numpy, spacy + modelo es_core_news_md
uvicorn api:app --host 0.0.0.0 --port 8000
```

El arranque tarda ~10 s (carga de spaCy). Ya no hace falta torch ni
scikit-learn en producción.

---

## Estructura

```
IA/
├── api.py                    # FastAPI: define los endpoints (uvicorn api:app)
├── funciones.py              # carga spaCy y los modelos una sola vez; une api.py con los modelos
├── prediccion.py             # modelo de predicción (n-gramas Kneser-Ney) + personalización por usuario
├── correccion.py             # corrector (etiquetador de ediciones en numpy) + corrección básica de respaldo
├── morfologia.py             # conjugación, género/número, tildes, plurales (reglas, sin aprendizaje)
├── modelo_prediccion.npz     # pesos del modelo de predicción (arrays numpy)
├── modelo_prediccion.json    # vocabulario y contextos del modelo de predicción
├── requirements.txt          # dependencias de producción
├── Procfile                  # comando de arranque (Railway/Heroku)
├── DOCUMENTACION.md          # este archivo
├── scripts/                  # todo lo que NO se usa en producción
│   ├── corpus_caa.py             # genera datos/corpus_caa.txt (frases correctas de CAA)
│   ├── entrenar_prediccion.py    # entrena modelo_prediccion.{npz,json}
│   ├── entrenar_correccion.py    # entrena modelo_correccion.{npz,json} + lexico_correccion.json
│   ├── descargar_tatoeba.py      # descarga oraciones de Tatoeba (solo para entrenar el corrector)
│   ├── probar_endpoints.py       # prueba de punta a punta de todos los endpoints
│   ├── requirements-entrenamiento.txt
│   └── datos/
│       ├── corpus_caa.txt        # 45.000 frases generadas
│       └── frases_curadas.txt    # 2.602 frases escritas a mano (de los datasets anteriores)
└── archivos_viejos/          # modelos y código de versiones anteriores (no se usan)
    ├── prediccion_mlp/           # MLP de scikit-learn (modelo_base.pkl, ...) y sus scripts
    ├── correccion_seq2seq/       # seq2seq GRU anterior (modelo_correccion.pt, ...) y sus datasets
    ├── correccion_legacy/        # primera versión del corrector
    └── API_DOCS_anterior.txt     # documentación vieja (reemplazada por este archivo)
```

Archivos que se generan en ejecución y no se versionan (`.gitignore`):
`modelos_usuarios/` (historial por usuario), `scripts/datos/externos/`
(Tatoeba descargado) y `scripts/datos/cache/`.

### Cómo se conectan

```
api.py ──importa──> funciones.py ──carga──> spaCy es_core_news_md (sin parser/NER)
                         │
                         ├──> prediccion.Predictor   (modelo_prediccion.npz/.json, modelos_usuarios/)
                         │         └── usa morfologia.quitar_tildes
                         └──> correccion.Corrector   (modelo_correccion.npz/.json, lexico_correccion.json)
                                   └── usa morfologia (conjugación, concordancia, tildes)
                              si faltan esos archivos -> correccion.correccion_basica

scripts/corpus_caa.py ──> datos/corpus_caa.txt ──┬──> entrenar_prediccion.py ──> modelo_prediccion.*
datos/frases_curadas.txt ────────────────────────┤
descargar_tatoeba.py ──> datos/externos/ ────────┴──> entrenar_correccion.py ──> modelo_correccion.*, lexico_correccion.json
```

`morfologia.py` lo usan tanto los scripts de entrenamiento (para generar
frases con concordancia correcta) como el corrector en producción (para
producir la otra forma de una palabra), así las dos etapas siguen las mismas
reglas. `correccion.py` también exporta las funciones de rasgos
(`rasgos_doc`, `ids_doc`, `doc_desde_palabras`) que usa el script de
entrenamiento, para que entrenamiento y producción calculen exactamente lo
mismo.

---

## Endpoints

### `GET /` y `GET /ping`
Chequeo de salud. Respuesta: `{"status": "ok"}`. `/ping` es para que
UptimeRobot mantenga despierto el servidor gratuito.

### `POST /predecir`
Entrada:
```json
{"user_id": "001", "palabras": ["quiero", "ir", "al"]}
```
- `user_id` (string, obligatorio).
- `palabras` (lista de strings, opcional, default `[]`): las últimas palabras
  que escribió el usuario, en orden. Se usan las últimas 3. Si hay menos de 3,
  se interpreta que la frase recién empieza (lista vacía = todavía no escribió
  nada). Se aceptan mayúsculas, puntuación y elementos con varias palabras
  ("por favor").

Salida: **siempre** una lista de exactamente 3 palabras distintas, de mayor a
menor probabilidad (porcentaje 0–100 de la distribución completa, por eso no
suman 100):
```json
[{"palabra": "club", "probabilidad": 15.47},
 {"palabra": "zoológico", "probabilidad": 14.75},
 {"palabra": "parque", "probabilidad": 13.27}]
```
Tiempo de respuesta: < 1 ms de cómputo (~10 ms con el overhead HTTP).

### `POST /reentrenar`
Entrada:
```json
{"user_id": "001", "datos": [{"categoria": "Casa", "frase": ["quiero", "ver", "televisión"]}]}
```
`categoria` se acepta por compatibilidad pero no se usa. Cada `frase` es la
lista de palabras en el orden en que el usuario las tocó.

Salida: `{"status": "ok", "pares_entrenados": N}` (N = cantidad de pares
contexto → palabra siguiente sumados, incluido el inicio de frase) o
`{"status": "sin_datos"}` si no vino ninguna palabra.

Es acumulativo e instantáneo (milisegundos): suma conteos al historial del
usuario en `modelos_usuarios/<user_id>.json`. El `user_id` se sanea antes de
usarlo como nombre de archivo (no se puede escribir fuera de esa carpeta).
Las palabras nuevas del usuario (que no están en el vocabulario base) también
se empiezan a sugerir.

### `POST /corregir`
Entrada:
```json
{"palabras": ["quiero", "ir", "parque", "con", "mi", "mamá"]}
```
Salida: `{"frase": "Quiero ir al parque con mi mamá."}`

- Lista vacía → `""`. Una sola palabra → se devuelve igual.
- Si alguna palabra trae `?` (o la frase empieza con un interrogativo) se
  devuelve entre `¿...?`.
- La salida mantiene siempre las palabras del usuario en su orden.

---

## Modelos

### Predicción: n-gramas con Kneser-Ney (`prediccion.py`)
**Reemplaza** al MLP de scikit-learn anterior (que estaba sobreajustado a
plantillas: `["quiero","tomar","un"]` → "nuevo" 90%; ver `archivos_viejos/`).

- **Qué es:** modelo de lenguaje de 4-gramas (contexto de hasta 3 palabras)
  con suavizado Kneser-Ney interpolado y un token `<s>` de inicio de frase.
  Para un contexto nunca visto ("mañana vamos a") combina lo que sabe de los
  contextos más cortos ("vamos a", "a"), así generaliza a frases que no
  están en el corpus.
- **Palabras desconocidas:** se reemplazan por la palabra conocida sin tildes
  equivalente ("mama" → "mamá") o por la más parecida según los vectores de
  spaCy (coseno ≥ 0,55). Si no hay ninguna, se usa el contexto posterior.
- **Personalización:** la distribución base se mezcla con la del usuario con
  peso `c / (c + 2)`, donde `c` = veces que el usuario usó ese contexto.
- **Entrenamiento:** `python scripts/entrenar_prediccion.py`. Cuenta n-gramas
  sobre `corpus_caa.txt` (45.000 frases) + `frases_curadas.txt` (2.602, peso
  3). Descuentos de Ney por orden. Resultado: 2.437 palabras, 99.144
  contextos, ~2,7 MB.
- **Velocidad:** la predicción es una suma de arrays numpy, < 1 ms.

### Corrección: etiquetador de ediciones (`correccion.py`)
**Reemplaza** al seq2seq anterior, que generaba la frase desde cero y producía
frases incoherentes ("Quiero la agua, el fría y por el favor.").

- **Qué es:** una red BiGRU de 2 capas (1,48 M parámetros) que, en vez de
  reescribir la frase, predice para cada palabra del usuario:
  1. qué palabra funcional falta antes (nada, "el", "a la", "de", "que", una
     coma, ...: 72 opciones cerradas aprendidas del corpus);
  2. qué hacer con la palabra: dejarla, cambiarle género/número, cambiar la
     persona del verbo, ponerle tilde, cambiar la preposición o borrarla si es
     una palabra funcional sobrante;
  3. si la frase es una pregunta.
  Entradas por palabra: embedding propio, sufijo, vector de spaCy, POS y
  morfología de spaCy y rasgos de léxico (género conocido del sustantivo,
  etc.).
- **Por qué no puede devolver algo sin sentido:** la salida siempre son las
  palabras del usuario en su orden; solo se insertan palabras funcionales de
  la lista cerrada o se usa otra forma de la misma palabra (generada por
  reglas en `morfologia.py`); cada edición necesita alta confianza (umbrales
  elegidos para ≥ 97 % de precisión en validación); hay un tope de ediciones
  por frase y chequeos estructurales (no "la el", no terminar en
  preposición). Si algo falla, se devuelve la frase del usuario solo con
  mayúscula y punto.
- **Entrenamiento:** `python scripts/entrenar_correccion.py`. Toma frases
  correctas (corpus CAA, frases curadas y 90.000 oraciones de
  [Tatoeba](https://tatoeba.org), CC BY 2.0 FR), las rompe a propósito con
  errores típicos (falta un artículo/preposición/contracción/"que"/coma,
  género o número equivocado, verbo en otra persona que su sujeto explícito,
  falta una tilde, sobra una palabra funcional, preposición cambiada) y la
  red aprende a deshacerlos. Como las roturas son nuestras, cada etiqueta se
  conoce exactamente. 179.505 ejemplos de entrenamiento y 6.000 de
  validación (frases nunca vistas). Se entrena en PyTorch y se exporta a
  numpy: la inferencia no necesita torch y tarda pocos milisegundos.

---

## Pruebas

```bash
cd IA
pip install -r scripts/requirements-entrenamiento.txt
python scripts/probar_endpoints.py
```
Prueba todos los endpoints con frases que **no están** en ningún dataset de
entrenamiento (el script lo verifica): 54 contextos de `/predecir` (1, 2 y 3
palabras, < 100 ms, siempre 3 palabras), 34 frases de `/corregir` (< 2 s, sin
reordenar ni inventar palabras, comparadas con la corrección esperada),
`/reentrenar` (acumulativo, palabras nuevas, `user_id` malicioso), `/` y
`/ping`. Sale con código 1 si algo falla.

---

## Pendientes

1. **Terminar de entrenar el corrector y subir sus archivos:**
   ```bash
   cd IA
   python -I scripts/descargar_tatoeba.py      # solo la primera vez
   python -I scripts/entrenar_correccion.py    # ~35 min en CPU; genera los 3 archivos
   python scripts/probar_endpoints.py          # verificar antes de subir
   git add modelo_correccion.npz modelo_correccion.json lexico_correccion.json
   ```
   Con esos archivos presentes, `funciones.py` usa el corrector completo
   automáticamente (sin cambiar código).
2. Correr `scripts/probar_endpoints.py` completo con el corrector entrenado y
   ajustar umbrales o el corpus según los casos que no salgan como se espera.
