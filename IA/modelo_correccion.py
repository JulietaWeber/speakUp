"""
Entrena un modelo de corrección de frases para CAA: recibe palabras sueltas
seleccionadas por el usuario (en cualquier orden) y aprende a producir la
frase natural en español correspondiente, usando EXACTAMENTE esas palabras
(reordenadas y conjugadas) más el glue gramatical mínimo (artículos,
preposiciones, pronombres, etc. - ver gramatica.py).

Arquitectura: seq2seq encoder-decoder con atención (Bahdanau) sobre GRUs de
una sola capa y una sola dirección, liviano para que la inferencia sea
rápida en el servidor:
- Encoder: cada palabra de entrada se representa con su vector de spaCy
  (embeddings preentrenados en español). Esto es clave para generalizar a
  frases nunca vistas: si el usuario elige un sinónimo o una palabra nueva,
  su vector va a estar cerca de palabras que el modelo sí vio entrenando.
- Decoder: GRU con atención que genera la frase palabra por palabra a partir
  de un vocabulario de salida aprendido del dataset.
- Restricción de vocabulario en inferencia: en cada paso de generación se
  enmascaran (logit = -inf) todos los tokens del vocabulario que no sean ni
  palabras funcionales cerradas ni derivados de alguna palabra de entrada.
  Así el modelo puede reordenar y conjugar, pero estructuralmente NO puede
  inventar contenido nuevo, incluso si nunca vio ese input exacto en el
  dataset de entrenamiento.

Se ejecuta como script para entrenar y guardar los pesos en
modelo_correccion.pt. Las clases (Encoder, Attention, Decoder) y la función
de inferencia `corregir_frase` se importan desde funciones.py para servir el
modelo en la API.
"""

import json
import re
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from collections import Counter

from conjugacion import (
    componer_clausula, es_infinitivo, es_verbo, infinitivo_sin_gobierno,
    tiene_verbo_conjugado,
)

from gramatica import (
    lema, es_permitida, cubre_entrada, bien_formada, palabras_obligatorias, token_cubre,
    CONJUNCIONES, FUNCIONALES,
)

random.seed(42)
torch.manual_seed(42)

DEVICE = torch.device("cpu")

PAD, SOS, EOS, UNK = "<pad>", "<sos>", "<eos>", "<unk>"
FIN_DE_FRASE = {".", "!", "?"}

HIDDEN_SIZE = 64
EMB_SIZE = 48
DROPOUT = 0.15
MAX_LEN_SALIDA = 20  # tope de tokens al generar, evita loops infinitos (el
                      # dataset actual no supera 15 tokens de salida)

# ── Tokenización de la frase de salida ──────────────────────────────────────
# Separamos palabras y signos de puntuación como tokens distintos para que el
# vocabulario de salida no explote (p. ej. "agua" y "agua." serían el mismo).

def tokenizar_salida(texto):
    return re.findall(r"\w+|[^\w\s]", texto, flags=re.UNICODE)

def detokenizar_salida(tokens):
    no_espacio_antes = set(".,;:!?)»”’")
    no_espacio_despues = set("¿¡(«“‘")
    texto = ""
    for tok in tokens:
        if not texto:
            texto = tok
        elif tok in no_espacio_antes or texto[-1] in no_espacio_despues:
            texto += tok
        else:
            texto += " " + tok
    return texto

# ── Vocabulario de salida ────────────────────────────────────────────────────

class Vocabulario:
    def __init__(self, oraciones_tokenizadas):
        especiales = [PAD, SOS, EOS, UNK]
        vistos = set()
        palabras = []
        for tokens in oraciones_tokenizadas:
            for t in tokens:
                if t not in vistos:
                    vistos.add(t)
                    palabras.append(t)
        self.idx2tok = especiales + sorted(palabras)
        self.tok2idx = {t: i for i, t in enumerate(self.idx2tok)}

    def __len__(self):
        return len(self.idx2tok)

    def encode(self, tokens):
        unk = self.tok2idx[UNK]
        ids = [self.tok2idx.get(t, unk) for t in tokens]
        return [self.tok2idx[SOS]] + ids + [self.tok2idx[EOS]]

    def decode(self, ids):
        tokens = []
        for i in ids:
            tok = self.idx2tok[i]
            if tok == EOS:
                break
            if tok in (SOS, PAD):
                continue
            tokens.append(tok)
        return tokens

# ── Vectorización de la entrada con spaCy ────────────────────────────────────

_cache_vectores = {}

def vector_palabra(nlp, palabra):
    palabra = palabra.lower()
    if palabra not in _cache_vectores:
        _cache_vectores[palabra] = nlp(palabra).vector.astype(np.float32)
    return _cache_vectores[palabra]

def vectorizar_entrada(nlp, palabras):
    """Convierte una lista de palabras sueltas en una matriz (largo, dim_spacy)."""
    return np.stack([vector_palabra(nlp, p) for p in palabras])

# ── Arquitectura ─────────────────────────────────────────────────────────────
# Encoder unidireccional de una sola capa (más liviano que un GRU bidireccional
# de 2 capas: la mitad de los parámetros recurrentes y la mitad del cómputo en
# cada forward pass), suficiente para bolsas de palabras cortas como las de CAA.

class Encoder(nn.Module):
    def __init__(self, input_size, hidden_size=HIDDEN_SIZE, dropout=DROPOUT):
        super().__init__()
        self.hidden_size = hidden_size
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, lengths):
        x = self.dropout(x)
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths, batch_first=True, enforce_sorted=False
        )
        outputs, hidden = self.gru(packed)
        outputs, _ = nn.utils.rnn.pad_packed_sequence(outputs, batch_first=True)
        return outputs, hidden

class Attention(nn.Module):
    def __init__(self, hidden_size=HIDDEN_SIZE):
        super().__init__()
        self.attn = nn.Linear(hidden_size * 2, hidden_size)
        self.v = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, decoder_hidden, encoder_outputs, mask):
        seq_len = encoder_outputs.size(1)
        dec_h = decoder_hidden.squeeze(0).unsqueeze(1).repeat(1, seq_len, 1)
        energia = torch.tanh(self.attn(torch.cat([dec_h, encoder_outputs], dim=2)))
        scores = self.v(energia).squeeze(2)
        scores = scores.masked_fill(mask == 0, -1e10)
        pesos = F.softmax(scores, dim=1)
        contexto = torch.bmm(pesos.unsqueeze(1), encoder_outputs)
        return contexto, pesos

class Decoder(nn.Module):
    def __init__(self, vocab_size, hidden_size=HIDDEN_SIZE, emb_size=EMB_SIZE, dropout=DROPOUT):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_size, padding_idx=0)
        self.attention = Attention(hidden_size)
        self.gru = nn.GRU(emb_size + hidden_size, hidden_size, batch_first=True)
        self.out = nn.Linear(hidden_size * 2 + emb_size, vocab_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, token_entrada, hidden, encoder_outputs, mask):
        embedded = self.dropout(self.embedding(token_entrada).unsqueeze(1))
        contexto, pesos = self.attention(hidden, encoder_outputs, mask)
        entrada_gru = torch.cat([embedded, contexto], dim=2)
        salida, hidden = self.gru(entrada_gru, hidden)
        logits = self.out(torch.cat([salida.squeeze(1), contexto.squeeze(1), embedded.squeeze(1)], dim=1))
        return logits, hidden, pesos

# ── Restricción de vocabulario en inferencia ─────────────────────────────────

def _mascara_vocabulario(nlp, vocab_salida, palabras):
    """Devuelve un tensor (vocab,) con 0.0 en los tokens que el decoder tiene
    permitido generar y -inf en el resto: palabras funcionales cerradas
    (gramatica.FUNCIONALES), puntuación, <eos>, y cualquier token cuyo lema
    coincida con el de alguna palabra de entrada. Esto es lo que impide que
    el modelo "invente" contenido que el usuario no seleccionó, incluso para
    combinaciones de palabras que nunca vio en el dataset de entrenamiento."""
    lemas_entrada = {lema(nlp, p) for p in palabras}
    mask = torch.full((len(vocab_salida),), float("-inf"))
    for idx, tok in enumerate(vocab_salida.idx2tok):
        if tok in (PAD, SOS, UNK):
            continue
        if tok == EOS:
            mask[idx] = 0.0
            continue
        if es_permitida(nlp, tok, lemas_entrada):
            mask[idx] = 0.0
    return mask

# ── Inferencia (usada acá para evaluar y en funciones.py para servir) ────────

def corregir_frase(nlp, encoder, decoder, vocab_salida, palabras):
    """Arma una frase gramaticalmente correcta en español a partir de
    `palabras`, reordenándolas y conjugándolas, pero sin agregar contenido
    que el usuario no seleccionó (ver `_mascara_vocabulario`).

    Si `palabras` tiene un solo elemento no hay nada que corregir ni
    reordenar: se devuelve tal cual. Si el modelo no logra usar todas las
    palabras de una sola vez (frases largas), se parte la frase en tramos, se
    corrige cada tramo y se unen; un tramo que no se puede armar queda literal."""
    palabras = [p.strip() for p in palabras if isinstance(p, str) and p.strip()]
    if len(palabras) <= 1:
        return palabras[0] if palabras else ""
    frase, _ = _corregir_recursivo(nlp, encoder, decoder, vocab_salida, tuple(palabras), False, {})
    return frase

def _corregir_recursivo(nlp, encoder, decoder, vocab_salida, palabras, causa, memo):
    """Devuelve (frase, palabras_sin_procesar): cuántas palabras quedaron
    literales, sin que el modelo las conjugue. Se usa para elegir el corte que
    mejor aprovecha al modelo. `causa` indica que el tramo viene después de
    "porque" (afecta el tiempo verbal de componer_clausula)."""
    clave = (palabras, causa)
    if clave in memo:
        return memo[clave]
    frase = _generar(nlp, encoder, decoder, vocab_salida, list(palabras))
    if frase is None:
        # El modelo no pudo (verbo sin conjugar, palabras que no conoce...):
        # si es una cláusula simple, se arma por reglas conjugando el verbo.
        frase_reglas = componer_clausula(nlp, palabras, causa)
        if frase_reglas is not None:
            memo[clave] = (frase_reglas, 0)
            return memo[clave]
    # El modelo rinde mucho mejor con frases cortas (casi todo su entrenamiento
    # tiene <= 5 palabras): en las largas, aunque devuelva algo válido, se
    # prefiere partir si todos los tramos pueden armarse con el modelo.
    corte = None
    if len(palabras) >= 4 and (frase is None or len(palabras) > MAX_PALABRAS_DIRECTO):
        corte = _mejor_corte(nlp, encoder, decoder, vocab_salida, palabras, causa, memo)
    if frase is not None and (corte is None or corte[1] > 0):
        resultado = (frase, 0)
    elif corte is not None:
        resultado = corte
    else:
        resultado = (_frase_literal(palabras), len(palabras))
    memo[clave] = resultado
    return resultado

MAX_PALABRAS_DIRECTO = 5

def _mejor_corte(nlp, encoder, decoder, vocab_salida, palabras, causa, memo):
    """Prueba los cortes candidatos y devuelve (frase, palabras_sin_procesar)
    del que deja menos palabras literales."""
    mejor = None
    for izq, conector, der in _cortes(nlp, palabras):
        f_izq, lit_izq = _sub(nlp, encoder, decoder, vocab_salida, izq, causa, memo)
        f_der, lit_der = _sub(nlp, encoder, decoder, vocab_salida, der, conector == "porque", memo)
        union = f" {conector} " if conector else ", "
        candidato = (f_izq.rstrip(".") + union + f_der[0].lower() + f_der[1:], lit_izq + lit_der)
        if mejor is None or candidato[1] < mejor[1]:
            mejor = candidato
        if mejor[1] == 0:
            break
    return mejor

def _sub(nlp, encoder, decoder, vocab_salida, palabras, causa, memo):
    if len(palabras) == 1:
        return _frase_literal(palabras), 1
    return _corregir_recursivo(nlp, encoder, decoder, vocab_salida, palabras, causa, memo)

MAX_CORTES = 3  # candidatos de corte a probar por tramo (acota la latencia)
NO_SEPARAR_DE = {"querer", "quiero", "poder", "necesitar", "deber", "saber", "soler", "intentar", "ir", "no", "tener"}

def _cortes(nlp, palabras):
    """Candidatos para partir una frase que el modelo no pudo armar entera,
    como (izquierda, conector, derecha), del más al menos prometedor.
    Si hay conjunciones (porque, y, pero...) se corta en ellas y la conjunción
    se conserva como nexo; si no, se corta antes de un verbo o, en su defecto,
    en cualquier posición. En todos los casos, cerca del medio primero."""
    n = len(palabras)
    medio = n / 2
    conj = [i for i in range(1, n - 1) if palabras[i].lower() in CONJUNCIONES]
    if conj:
        orden = sorted(conj, key=lambda k: abs(k - medio))[:MAX_CORTES]
        return [(palabras[:i], palabras[i], palabras[i + 1:]) for i in orden]
    # No cortar entre un modal y su complemento ("querer | ir", "poder | comer")
    posibles = [i for i in range(2, n - 1) if palabras[i - 1].lower() not in NO_SEPARAR_DE]
    verbos = [i for i in posibles if es_verbo(nlp, palabras[i])]
    orden = sorted(verbos, key=lambda k: abs(k - medio))[:MAX_CORTES]
    orden += [i for i in sorted(posibles, key=lambda k: abs(k - medio)) if i not in orden][: MAX_CORTES - len(orden)]
    return [(palabras[:i], None, palabras[i:]) for i in orden]

def _generar(nlp, encoder, decoder, vocab_salida, palabras):
    """Genera la frase con el modelo. Devuelve None si el resultado no usa
    todas las palabras obligatorias de la entrada."""
    encoder.eval()
    decoder.eval()
    eos_idx = vocab_salida.tok2idx[EOS]
    with torch.no_grad():
        vecs = vectorizar_entrada(nlp, palabras)
        x = torch.tensor(vecs, dtype=torch.float32).unsqueeze(0)
        lengths = [len(palabras)]

        encoder_outputs, hidden = encoder(x, lengths)
        mask = torch.ones(1, encoder_outputs.size(1))
        mask_vocab = _mascara_vocabulario(nlp, vocab_salida, palabras)

        token = torch.tensor([vocab_salida.tok2idx[SOS]])
        prev_id = vocab_salida.tok2idx[SOS]
        bigramas_vistos = set()
        ids_generados = []
        requeridas = palabras_obligatorias(palabras)
        pendientes = set(requeridas)
        # Cada palabra de contenido se puede usar tantas veces como el usuario
        # la eligió (evita "tengo frío, tengo frío"); las funcionales, hasta 2.
        restante = dict(Counter(requeridas))
        usos_funcionales = Counter()
        cubre_cache = {}

        def palabras_que_cubre(tok):
            if tok not in cubre_cache:
                cubre_cache[tok] = [p for p in restante if token_cubre(nlp, tok, p)]
            return cubre_cache[tok]

        max_len = min(MAX_LEN_SALIDA, 2 * len(palabras) + 4)
        for _ in range(max_len):
            logits, hidden, _ = decoder(token, hidden, encoder_outputs, mask)
            logits = logits[0] + mask_vocab
            orden = torch.argsort(logits, descending=True)

            elegido = None
            for candidato in orden.tolist():
                if logits[candidato].item() == float("-inf"):
                    break  # ya no quedan candidatos permitidos
                if candidato == eos_idx:
                    if pendientes:
                        continue  # no se puede terminar sin usar todas las palabras
                    elegido = candidato
                    break
                tok = vocab_salida.idx2tok[candidato]
                if tok in FIN_DE_FRASE and pendientes:
                    continue  # no cerrar la frase antes de usar todas las palabras
                if (prev_id, candidato) in bigramas_vistos:
                    continue
                cubre = palabras_que_cubre(tok)
                if any(restante[p] == 0 for p in cubre):
                    continue  # ya se usó todas las veces que el usuario la eligió
                if not cubre and tok.lower() in FUNCIONALES and usos_funcionales[tok.lower()] >= 2:
                    continue
                elegido = candidato
                break
            if elegido is None or elegido == eos_idx:
                break

            bigramas_vistos.add((prev_id, elegido))
            ids_generados.append(elegido)
            tok_elegido = vocab_salida.idx2tok[elegido]
            cubre = palabras_que_cubre(tok_elegido)
            for p in cubre:
                restante[p] -= 1
                pendientes.discard(p)
            if not cubre and tok_elegido.lower() in FUNCIONALES:
                usos_funcionales[tok_elegido.lower()] += 1
            if tok_elegido in FIN_DE_FRASE:
                break  # la frase termina en el primer punto: nada de texto extra
            prev_id = elegido
            token = torch.tensor([elegido])

        tokens = vocab_salida.decode(ids_generados)
        # Si el modelo no usó todas las palabras del usuario (típico en frases
        # largas o con palabras que nunca vio), su salida no es confiable:
        # mejor no devolverla que devolver una frase con contenido perdido.
        if not tokens or not cubre_entrada(nlp, tokens, palabras) or not bien_formada(tokens):
            return None
        # Si el usuario eligió un verbo en infinitivo, la frase tiene que
        # tener algún verbo conjugado ("No esta noche dormir." no sirve).
        infinitivos = {p.lower() for p in palabras if es_infinitivo(nlp, p)}
        if infinitivos:
            frase = detokenizar_salida(tokens)
            if not tiene_verbo_conjugado(nlp, frase) or infinitivo_sin_gobierno(nlp, frase, infinitivos):
                return None
        return detokenizar_salida(tokens)

def _frase_literal(palabras):
    """Fallback determinista: exactamente las palabras recibidas, en el orden
    recibido, sin agregar nada salvo mayúscula inicial y punto final."""
    texto = " ".join(palabras)
    return texto[0].upper() + texto[1:] + "."

# ── Entrenamiento ─────────────────────────────────────────────────────────────

def _pares_compuestos(pares, cantidad):
    """Genera ejemplos largos uniendo dos pares (entrada, salida) del dataset:
    entrada = palabras de A + conector (si es una palabra) + palabras de B;
    salida = A sin punto + conector + B con minúscula inicial."""
    simples = [
        (pin, pout) for pin, pout in pares
        if len(pin) <= 5 and pout[-1] == "." and pout[0].isalpha() and "¿" not in pout
    ]
    conectores = [("y", ["y"], ["y"]), ("porque", ["porque"], ["porque"]), (",", [], [","])]
    pesos = [0.4, 0.3, 0.3]
    compuestos = []
    intentos = 0
    while len(compuestos) < cantidad and intentos < cantidad * 20:
        intentos += 1
        (a_in, a_out), (b_in, b_out) = random.sample(simples, 2)
        _, extra_in, extra_out = random.choices(conectores, pesos)[0]
        if "porque" in a_in or "porque" in b_in or set(a_in) & set(b_in):
            continue
        entrada = a_in + extra_in + b_in
        if len(entrada) > 10:
            continue
        salida = a_out[:-1] + extra_out + [b_out[0].lower()] + b_out[1:]
        compuestos.append((entrada, salida))
    return compuestos

def entrenar():
    import spacy

    print("Cargando spaCy...")
    nlp = spacy.load("es_core_news_md")
    dim_spacy = nlp.vocab.vectors_length or len(nlp("agua").vector)
    print(f"spaCy cargado (dim={dim_spacy})\n")

    print("Cargando dataset...")
    pares = []
    with open("dataset_correccion.jsonl", "r", encoding="utf-8") as f:
        for linea in f:
            par = json.loads(linea)
            pares.append((par["input"].split(), tokenizar_salida(par["output"])))
    print(f"Pares cargados: {len(pares)}")

    # Solo se entrena con ejemplos que usan TODAS las palabras de la entrada:
    # los que descartan palabras le enseñarían al modelo justo lo que la API
    # no debe hacer (ver gramatica.cubre_entrada).
    pares = [(pin, pout) for pin, pout in pares if cubre_entrada(nlp, pout, pin)]
    print(f"Pares que respetan todas las palabras: {len(pares)}")

    # Aumentación con frases largas: el dataset casi no tiene entradas de 6+
    # palabras, y con esas el modelo no generaliza. Se unen dos pares reales
    # con "y", "porque" o coma, conservando el orden de cada cláusula.
    pares += _pares_compuestos(pares, cantidad=3000)
    print(f"Con frases compuestas: {len(pares)}\n")

    vocab_salida = Vocabulario([out for _, out in pares])
    print(f"Vocabulario de salida: {len(vocab_salida)} tokens\n")

    print("Vectorizando entradas con spaCy (con caché por palabra)...")
    ejemplos = []
    for palabras_in, tokens_out in pares:
        vecs = vectorizar_entrada(nlp, palabras_in)
        ids_out = vocab_salida.encode(tokens_out)
        ejemplos.append((vecs, ids_out))
    print(f"Palabras únicas vectorizadas: {len(_cache_vectores)}\n")

    random.shuffle(ejemplos)
    corte = int(len(ejemplos) * 0.9)
    train_set, val_set = ejemplos[:corte], ejemplos[corte:]
    print(f"Train: {len(train_set)} | Val: {len(val_set)}\n")

    encoder = Encoder(dim_spacy).to(DEVICE)
    decoder = Decoder(len(vocab_salida)).to(DEVICE)
    optimizador = torch.optim.Adam(
        list(encoder.parameters()) + list(decoder.parameters()), lr=1e-3
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizador, mode="min", factor=0.5, patience=4
    )
    pad_idx = vocab_salida.tok2idx[PAD]
    criterio = nn.CrossEntropyLoss(ignore_index=pad_idx, label_smoothing=0.1)

    def hacer_batch(muestras):
        muestras = sorted(muestras, key=lambda m: len(m[0]), reverse=True)
        lengths_in = [len(m[0]) for m in muestras]
        max_in = max(lengths_in)
        max_out = max(len(m[1]) for m in muestras)

        batch_x = np.zeros((len(muestras), max_in, dim_spacy), dtype=np.float32)
        batch_y = np.full((len(muestras), max_out), pad_idx, dtype=np.int64)
        for i, (vecs, ids_out) in enumerate(muestras):
            batch_x[i, : len(vecs)] = vecs
            batch_y[i, : len(ids_out)] = ids_out

        x = torch.tensor(batch_x)
        y = torch.tensor(batch_y)
        mask = torch.zeros(len(muestras), max_in)
        for i, l in enumerate(lengths_in):
            mask[i, :l] = 1
        return x, lengths_in, mask, y

    EPOCHS = 80
    BATCH_SIZE = 32
    TEACHER_FORCING = 0.5

    print("Entrenando...")
    mejor_val_loss = float("inf")
    for epoch in range(1, EPOCHS + 1):
        encoder.train()
        decoder.train()
        random.shuffle(train_set)
        loss_total = 0.0

        for i in range(0, len(train_set), BATCH_SIZE):
            batch = train_set[i : i + BATCH_SIZE]
            x, lengths_in, mask, y = hacer_batch(batch)

            optimizador.zero_grad()
            encoder_outputs, hidden = encoder(x, lengths_in)

            token = y[:, 0]  # <sos>
            loss = 0.0
            pasos = y.size(1) - 1
            for t in range(1, y.size(1)):
                logits, hidden, _ = decoder(token, hidden, encoder_outputs, mask)
                loss = loss + criterio(logits, y[:, t])
                usar_teacher = random.random() < TEACHER_FORCING
                token = y[:, t] if usar_teacher else logits.argmax(1)

            loss = loss / pasos
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(encoder.parameters()) + list(decoder.parameters()), 1.0
            )
            optimizador.step()
            loss_total += loss.item() * len(batch)

        loss_train = loss_total / len(train_set)

        encoder.eval()
        decoder.eval()
        with torch.no_grad():
            val_loss_total = 0.0
            for i in range(0, len(val_set), BATCH_SIZE):
                batch = val_set[i : i + BATCH_SIZE]
                x, lengths_in, mask, y = hacer_batch(batch)
                encoder_outputs, hidden = encoder(x, lengths_in)
                token = y[:, 0]
                loss = 0.0
                pasos = y.size(1) - 1
                for t in range(1, y.size(1)):
                    logits, hidden, _ = decoder(token, hidden, encoder_outputs, mask)
                    loss = loss + criterio(logits, y[:, t])
                    token = logits.argmax(1)
                val_loss_total += (loss.item() / pasos) * len(batch)
            loss_val = val_loss_total / max(len(val_set), 1)

        scheduler.step(loss_val)

        if epoch % 5 == 0 or epoch == 1 or epoch == EPOCHS:
            lr_actual = optimizador.param_groups[0]["lr"]
            print(f"Epoch {epoch:3d} | train_loss={loss_train:.4f} | val_loss={loss_val:.4f} | lr={lr_actual:.2e}")

        if loss_val < mejor_val_loss:
            mejor_val_loss = loss_val
            torch.save(
                {
                    "encoder_state": encoder.state_dict(),
                    "decoder_state": decoder.state_dict(),
                    "tok2idx": vocab_salida.tok2idx,
                    "idx2tok": vocab_salida.idx2tok,
                    "dim_spacy": dim_spacy,
                    "hidden_size": HIDDEN_SIZE,
                    "emb_size": EMB_SIZE,
                },
                "modelo_correccion.pt",
            )

    print(f"\nMejor val_loss: {mejor_val_loss:.4f}")
    print("Modelo guardado en modelo_correccion.pt\n")

    # ── Prueba rápida con frases variadas (algunas no vistas en el dataset) ──
    print("-- Prueba de correccion --")
    checkpoint = torch.load("modelo_correccion.pt", weights_only=False)
    vocab_final = Vocabulario([])
    vocab_final.tok2idx = checkpoint["tok2idx"]
    vocab_final.idx2tok = checkpoint["idx2tok"]
    encoder_final = Encoder(dim_spacy)
    decoder_final = Decoder(len(vocab_final))
    encoder_final.load_state_dict(checkpoint["encoder_state"])
    decoder_final.load_state_dict(checkpoint["decoder_state"])

    ejemplos_prueba = [
        ["mamá", "agua", "querer"],
        ["doler", "cabeza"],
        ["escuela", "no", "querer", "ir"],
        ["amigo", "jugar", "querer", "parque"],
        ["yo", "querer", "comer", "pizza", "noche"],
        ["triste", "estar", "hoy"],
        ["agua"],
    ]
    for palabras in ejemplos_prueba:
        frase = corregir_frase(nlp, encoder_final, decoder_final, vocab_final, palabras)
        print(f"{palabras} -> {frase}")

if __name__ == "__main__":
    entrenar()
