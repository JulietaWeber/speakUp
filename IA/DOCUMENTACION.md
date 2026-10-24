# SpeakUp — API de IA

Documentación para code review. `IA/` es un servicio FastAPI que el backend
de SpeakUp usa para:

1. **Predecir** las próximas 3 palabras mientras el usuario arma una frase en
   el tablero de CAA (`POST /predecir`).
2. **Personalizar** esa predicción con las frases de cada usuario
   (`POST /reentrenar`).
3. **Completar y corregir** la frase armada (`POST /corregir`): deduce la
   frase completa a partir de los pictogramas elegidos (`["triste"]` →
   "Estoy triste.") y hace correcciones mínimas, sin perder nunca una
   palabra del usuario.

> **Estado:** los cuatro endpoints están terminados, entrenados y probados
> (`scripts/probar_endpoints.py` pasa todos los chequeos obligatorios). Si
> faltaran `modelo_correccion.npz`, `modelo_correccion.json` o
> `lexico_correccion.json`, la API arranca igual y `/corregir` usa la
> **corrección básica** (las palabras del usuario con contracciones, mayúscula
> y punto). Ver [Limitaciones conocidas](#limitaciones-conocidas).

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
├── modelo_correccion.npz     # pesos de la red de corrección (arrays numpy)
├── modelo_correccion.json    # vocabularios, etiquetas de inserción y umbrales del corrector
├── lexico_correccion.json    # léxico del corrector: género, tildes, verbos
├── requirements.txt          # dependencias de producción
├── Procfile                  # comando de arranque (Railway/Heroku)
├── DOCUMENTACION.md          # este archivo
├── scripts/                  # todo lo que NO se usa en producción
│   ├── corpus_caa.py             # genera datos/corpus_caa.txt (frases correctas de CAA)
│   ├── dataset_completar.py      # genera datos/completar_frases.tsv (pictogramas -> frase completa)
│   ├── entrenar_prediccion.py    # entrena modelo_prediccion.{npz,json}
│   ├── entrenar_correccion.py    # entrena modelo_correccion.{npz,json} + lexico_correccion.json
│   ├── descargar_tatoeba.py      # descarga oraciones de Tatoeba (opcional, solo para entrenar el corrector)
│   ├── probar_endpoints.py       # prueba de punta a punta de todos los endpoints
│   ├── requirements-entrenamiento.txt
│   └── datos/
│       ├── corpus_caa.txt        # 47.995 frases generadas
│       ├── frases_curadas.txt    # 2.602 frases escritas a mano (de los datasets anteriores)
│       └── completar_frases.tsv  # 115.853 pares pictogramas -> frase completa
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
descargar_tatoeba.py ──> datos/externos/ ────────┼──> entrenar_correccion.py ──> modelo_correccion.*, lexico_correccion.json
dataset_completar.py ──> datos/completar_frases.tsv ┘   (solo el corrector)
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
Entrada: los pictogramas que fue eligiendo el usuario, en orden (cada
elemento puede tener varias palabras: `"tengo hambre"`, `"por favor"`).
```json
{"palabras": ["mamá", "agua"]}
```
Salida: `{"frase": "Mamá, quiero agua."}`

| Entrada | Salida |
|---|---|
| `["triste"]` | `Estoy triste.` |
| `["pizza"]` | `Quiero pizza.` |
| `["mamá", "agua"]` | `Mamá, quiero agua.` |
| `["tengo hambre", "pizza"]` | `Tengo hambre, quiero pizza.` |
| `["quiero", "ir", "parque", "con", "mi", "mamá"]` | `Quiero ir al parque con mi mamá.` |
| `["hola", "chau", "pizza", "triste"]` (sin sentido) | `Hola chau pizza triste.` |

- **Regla fundamental:** las palabras del usuario aparecen siempre en la
  respuesta, en su orden. Solo se agregan palabras para completar o
  corregir; nunca se borra ni se reemplaza una palabra por otra. Lo único
  que puede cambiar es la forma de una palabra escrita a mano ("cansado" →
  "cansada", "mama" → "mamá"); las de los pictogramas de la app y las de un
  elemento de varias palabras quedan tal cual.
- Si no se puede deducir nada útil se devuelven las mismas palabras con
  mayúscula y punto (también una sola palabra: `["pelota"]` → `Pelota.`).
- Lista vacía → `""`.
- Si alguna palabra trae `?` (o la frase empieza con un interrogativo) se
  devuelve entre `¿...?`.

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
  sobre `corpus_caa.txt` (47.995 frases) + `frases_curadas.txt` (2.602, peso
  3). Descuentos de Ney por orden. Resultado: 2.479 palabras, 103.231
  contextos, ~2,8 MB.
- **Velocidad:** la predicción es una suma de arrays numpy, < 1 ms.

### Corrección: etiquetador de ediciones (`correccion.py`)
**Reemplaza** al seq2seq anterior, que generaba la frase desde cero y producía
frases incoherentes ("Quiero la agua, el fría y por el favor.").

- **Qué es:** una red BiGRU de 2 capas (1.493.205 parámetros) que, en vez de
  reescribir la frase, predice para cada palabra del usuario:
  1. qué falta antes de ella (nada, "el", "a la", "de", "que", una coma,
     "quiero", "estoy", ", quiero", "y comer", "porque"...: 118 opciones
     cerradas aprendidas del corpus y del dataset de completar frases);
  2. qué hacer con la palabra: dejarla, cambiarle género/número, cambiar la
     persona del verbo o ponerle tilde;
  3. si la frase es una pregunta.
  Entradas por palabra: embedding propio, sufijo, vector de spaCy, POS y
  morfología de spaCy y rasgos de léxico (género conocido del sustantivo,
  etc.). Hace **una sola pasada** por frase: una segunda pasada sobre la
  frase ya completada agregaba palabras de más ("Quiero estar porque estoy
  feliz.") y no mejoraba nada.
- **Por qué no puede devolver algo sin sentido ni perder palabras:** no
  existen ediciones de borrar ni de reemplazar, así que la salida siempre
  tiene las palabras del usuario en su orden. Solo se inserta texto de la
  lista cerrada o se usa otra forma de la misma palabra (generada por reglas
  en `morfologia.py`). Las palabras del vocabulario de la app
  (`palabras_fijas` en `modelo_correccion.json`) nunca se transforman, y
  nunca se inserta nada adentro de un elemento de varias palabras ("tengo
  hambre", "mirar tv"). Cada edición necesita alta confianza (umbrales
  elegidos para ≥ 97 % de precisión en validación), hay un tope de ediciones
  por frase y chequeos estructurales (no "la el", no terminar en
  preposición). Al final `conserva_palabras` vuelve a verificar la regla
  fundamental. Si algo falla, se devuelve la frase del usuario solo con
  mayúscula y punto.
- **Entrenamiento:** `python scripts/entrenar_correccion.py --rehacer`
  (~1 h 10 min en CPU; sin `--rehacer` reusa el dataset de
  `scripts/datos/cache/` y, si el entrenamiento se cortó, sigue desde el
  checkpoint de la última época). Usa dos fuentes:
  1. **Frases correctas rotas a propósito:** corpus CAA, frases curadas y
     90.000 oraciones de [Tatoeba](https://tatoeba.org) (CC BY 2.0 FR). Se
     rompen con errores típicos (falta un artículo/preposición/contracción/
     "que"/coma, género o número equivocado, verbo en otra persona que su
     sujeto explícito, falta una tilde) y la red aprende a deshacerlos. Como
     las roturas son nuestras, cada etiqueta se conoce exactamente.
  2. **Completar frases** (`scripts/datos/completar_frases.tsv`, generado por
     `scripts/dataset_completar.py`): 115.853 pares secuencia de pictogramas →
     frase completa, con todas las combinaciones de 1 a 3 palabras del
     vocabulario de la app y las de 4 que tienen sentido, más la mitad de esa
     cantidad de combinaciones de 4 sin sentido (que quedan iguales), y
     variantes con más comidas, bebidas, actividades, estados y vocativos.
     Las etiquetas salen de alinear las palabras del usuario dentro de la
     frase completa; el script verifica que todas aparezcan y que nada se
     inserte adentro de un elemento de varias palabras. Las secuencias de 1 y
     2 pictogramas se repiten (×30 y ×8) para que pesen en el entrenamiento.

  317.617 ejemplos de entrenamiento y 11.582 de validación (frases y
  secuencias nunca vistas), 12 épocas. Se entrena en PyTorch y se exporta a
  numpy: la inferencia no necesita torch y tarda pocos milisegundos.
  `--umbrales` recalcula solo los umbrales con el modelo exportado, sin
  reentrenar.
  - Tatoeba es **opcional**: si falta `scripts/datos/externos/tatoeba_es.txt`
    (p. ej. en una red que bloquea la descarga) el script entrena solo con el
    corpus CAA y las frases curadas, con más roturas por frase.
  - `--rapido`: versión de prueba (10.000 ejemplos, una rotura por frase,
    1.000 de validación, ~10 min). Corrige bastante peor: comparada con el
    modelo completo en las 39 frases de `probar_endpoints.py` dio 31/39 contra
    36/39, y en 46 frases nuevas 37/46 contra 42/46, con 8 correcciones mal
    hechas contra 1 ("con papas" → "con los papás", "viene mi abuela" →
    "viene a mi abuela", "Gracias, por ayudarme"...). El modelo que está en el
    repo es el del dataset completo.
- **Frases complementarias del corpus CAA** (`complementarias` en
  `corpus_caa.py`, ~3.000): construcciones que faltaban y producían
  correcciones malas. Sujeto después del verbo ("hoy viene mi abuela", "ya
  llegó el colectivo"): sin ellas el corrector agregaba la "a" personal ("viene
  a mi abuela"). "Papas" la comida ("pollo con papas"): sin ellas cambiaba
  "papas" por "papás". Se generan con otra semilla, así las 45.000 frases
  originales no cambian.
- **Léxico y verbos falsos:** el script arma `lexico_correccion.json` con el
  género de los sustantivos, las tildes y los verbos del corpus (de ahí sale
  el índice verbal que permite pasar "quiere" → "quiero"). Los verbos salen
  de los infinitivos que etiquetó spaCy y de los lemas de los verbos
  conjugados, para los que casi nunca aparecen en infinitivo ("duele" →
  doler, "prefiero" → preferir, "encanta" → encantar). Un lema solo cuenta si
  es una palabra real (tiene vector en spaCy) y tiene usos propios: el
  lematizador inventa lemas como "hayar" (de "haya", que ya es de haber).
  `filtrar_verbos` descarta los **verbos falsos**, que harían que palabras
  comunes se analicen como conjugaciones: sustantivos y nombres que spaCy
  etiquetó como infinitivo ("pajar" haría de "paja" un verbo, "billar",
  "caviar", "itziar"), variantes sin tilde ("reir" si está "reír") y verbos
  poco usados cuyas formas son casi siempre otras palabras ("piar" → "pie",
  "orar" → "oro", "mediar" → "media", "listar" → "listo"). Un verbo con al
  menos 10 usos conjugados en el corpus nunca se descarta ("ganar" aunque
  exista "ganas", "tardar" aunque exista "tarde"). Resultado: 1.109 verbos
  (326 encontrados por sus formas conjugadas) y 44 descartados.
- **Umbrales y métricas** (validación nunca vista: 5.999 frases rotas del
  corpus y 5.583 secuencias de 3-4 pictogramas, con la red numpy de
  producción): el script elige los umbrales más bajos que dan ≥ 97 % de
  precisión **en cada fuente por separado**, para que las secuencias de
  pictogramas (más fáciles) no bajen la precisión en frases escritas a mano.

  | Edición | Umbral | Precisión corpus | Recall corpus | Precisión completar | Recall completar |
  |---|---|---|---|---|---|
  | Insertar | 0,95 | 98,1 % | 32,5 % | 99,6 % | 99,4 % |
  | Transformar (género, persona, tilde) | 0,90 | 97,3 % | 72,1 % | — | — |

  Quedan exactamente bien el 49,0 % de las frases del corpus (el resto queda
  con alguna corrección sin hacer, casi nunca con una corrección mal hecha) y
  el 98,8 % de las secuencias de pictogramas. Pregunta / exclamación: 97,4 %
  de acierto.

---

## Pruebas

```bash
cd IA
pip install -r scripts/requirements-entrenamiento.txt
python scripts/probar_endpoints.py
```
Prueba todos los endpoints con frases que **no están** en ningún dataset de
entrenamiento (el script lo verifica): 54 contextos de `/predecir` (1, 2 y 3
palabras, < 100 ms, siempre 3 palabras), 39 frases de `/corregir`,
`/reentrenar` (acumulativo, palabras nuevas, `user_id` malicioso), `/` y
`/ping`. Sale con código 1 si algo falla.

Chequeos obligatorios de `/corregir`: responde en < 2 s; las palabras de
contenido de la salida son las del usuario, en su orden (se acepta otra
forma de la misma palabra: "cansado" → "cansada", "fue" → "fuimos"; los
artículos y preposiciones se pueden agregar, sacar o cambiar); y la salida no
queda peor armada que la entrada (artículos o preposiciones duplicados o
colgando, como "a la a la plaza").

Completar frases: los 3 ejemplos de referencia (`["triste"]` → `Estoy
triste.`, `["mamá", "agua"]` → `Mamá, quiero agua.`, `["pizza"]` → `Quiero
pizza.`) tienen que salir exactos; 25 casos más se muestran como referencia;
y un barrido sobre `completar_frases.tsv` (todas las secuencias de 1-2
pictogramas y 1.500 de 3-4 al azar) exige la regla fundamental y < 2 s en
cada una y muestra cuántas salen igual que el dataset.

Último resultado: todos los chequeos obligatorios pasan.
- Corrección: 34/39 iguales a la esperada, ~14 ms por frase (máx. 34 ms).
  Las 5 restantes quedan sin corregir, nunca mal corregidas: "mi mamá está
  cansado", "una muñeca nuevo", "un vaso agua con hielo", "podés prender luz"
  y la coma de "quiero agua fría, por favor".
- Completar: los 3 ejemplos exactos. En el barrido (4.238 secuencias,
  ~11 ms promedio, máx. 64 ms), el 98,3 % de las que tienen sentido salen
  igual que el dataset y el 99,9 % de las sin sentido quedan iguales. Las
  diferencias son casi siempre una coma o una "y" de menos en secuencias de
  4 pictogramas ("Estaba feliz contento ayer." en vez de "Estaba feliz y
  contento ayer.").

---

## Limitaciones conocidas

- El corrector prefiere no corregir a corregir mal: en frases escritas a mano
  hace ~33 % de las inserciones y ~72 % de las transformaciones que haría
  falta. Bajar los umbrales en `modelo_correccion.json` corrige más a costa de
  más errores (`--umbrales` los recalcula).
- Completar frases solo sabe armar lo que aparece en la gramática de
  `dataset_completar.py`: el vocabulario de la app y las palabras ampliadas
  (comidas, bebidas, actividades, estados, vocativos). Una palabra fuera de
  esa lista se completa solo si la red la asocia a una categoría por su vector
  de spaCy ("hamburguesa" → "Quiero hamburguesa.", "sándwich" → "Quiero
  sándwich."); si no, queda igual ("banana" → "Banana."). Un estado en la segunda
  parte de la frase ("pizza" + "triste") queda igual a propósito: enseñarlo
  hacía que la red agregara "porque estoy" delante de cualquier adjetivo
  ("Quiero agua porque estoy fría.").
- En secuencias de 4 pictogramas a veces falta una coma o una "y"
  ("Ayer quería dormir escuchar música, tío."). Nunca se pierde una palabra.
- La concordancia de un adjetivo lejos de su sustantivo ("mi mamá está
  cansado") todavía no alcanza la confianza necesaria.
- Las palabras con y sin tilde que existen las dos ("papas" / "papás",
  "esta" / "está") dependen del contexto; con poco contexto la red puede
  dudar y deja la palabra como está.
