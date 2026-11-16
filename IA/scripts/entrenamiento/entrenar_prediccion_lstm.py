import json
import os
import re
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split

# ── Configuración ──────────────────────────────────────────────────────────────
CORPUS_CAA      = "/mnt/user-data/attachments/78041025-87f6-5078-94e5-48948a1427b5/472e5950-attachment.txt"
COMPLETAR_TSV   = "/mnt/user-data/attachments/78041025-87f6-5078-94e5-48948a1427b5/e2363d80-completar_frases.tsv"
SALIDA_NPZ      = "/tmp/claude-0/-home-claude/78041025-87f6-5078-94e5-48948a1427b5/scratchpad/modelo_prediccion_lstm.npz"
SALIDA_JSON     = "/tmp/claude-0/-home-claude/78041025-87f6-5078-94e5-48948a1427b5/scratchpad/modelo_prediccion_lstm.json"

CONTEXTO        = 3       # palabras de contexto (X)
MIN_FREQ        = 2       # frecuencia mínima para entrar al vocabulario
EMB_DIM         = 64      # dimensión del embedding
HIDDEN_DIM      = 128     # dimensión del LSTM
N_CAPAS         = 1       # capas del LSTM
DROPOUT         = 0.2
BATCH_SIZE      = 512
EPOCHS          = 10
LR              = 1e-3
TEST_SPLIT      = 0.1     # 10% para test
SEED            = 42

PAD   = "<pad>"
UNK   = "<unk>"
INICIO = "<s>"

_PALABRA = re.compile(r"[a-záéíóúüñ]+")

torch.manual_seed(SEED)
np.random.seed(SEED)


# ── Datos ──────────────────────────────────────────────────────────────────────

def tokenizar(texto):
    return _PALABRA.findall(texto.lower())


def leer_corpus():
    frases = []
    # corpus_caa.txt
    with open(CORPUS_CAA, encoding="utf-8") as f:
        for linea in f:
            tokens = tokenizar(linea.strip())
            if tokens:
                frases.append(tokens)

    # completar_frases.tsv — columna "frase"
    with open(COMPLETAR_TSV, encoding="utf-8") as f:
        next(f)  # saltar header
        for linea in f:
            partes = linea.strip().split("\t")
            if len(partes) >= 2:
                tokens = tokenizar(partes[1])
                if tokens:
                    frases.append(tokens)

    print(f"Frases totales: {len(frases):,}")
    return frases


def construir_vocab(frases):
    from collections import Counter
    contador = Counter()
    for f in frases:
        contador.update(f)
    vocab = [PAD, UNK, INICIO] + [w for w, c in contador.most_common() if c >= MIN_FREQ]
    idx = {w: i for i, w in enumerate(vocab)}
    print(f"Vocabulario: {len(vocab):,} palabras (frecuencia mínima={MIN_FREQ})")
    return vocab, idx


def generar_pares(frases, idx):
    """
    X: secuencia de CONTEXTO palabras  (índices)
    Y: palabra siguiente               (índice)
    """
    unk_id = idx[UNK]
    inicio_id = idx[INICIO]
    X, Y = [], []
    for tokens in frases:
        # padding con <s> al principio
        seq = [inicio_id] * CONTEXTO + [idx.get(t, unk_id) for t in tokens]
        for i in range(CONTEXTO, len(seq)):
            X.append(seq[i - CONTEXTO:i])
            Y.append(seq[i])
    X = np.array(X, dtype=np.int64)
    Y = np.array(Y, dtype=np.int64)
    print(f"Pares X/Y generados: {len(X):,}")
    return X, Y


class PredDataset(Dataset):
    def __init__(self, X, Y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.Y = torch.tensor(Y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.Y[i]


# ── Modelo ─────────────────────────────────────────────────────────────────────

class ModeloLSTM(nn.Module):
    """
    Embedding + LSTM + capa de salida.
    Input:  (batch, CONTEXTO) índices de palabras
    Output: (batch, vocab_size) logits
    """
    def __init__(self, vocab_size, emb_dim, hidden_dim, n_capas, dropout):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=emb_dim,
            hidden_size=hidden_dim,
            num_layers=n_capas,
            batch_first=True,
            dropout=dropout if n_capas > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.salida = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        emb = self.dropout(self.embedding(x))       # (B, T, emb_dim)
        out, _ = self.lstm(emb)                     # (B, T, hidden_dim)
        logits = self.salida(self.dropout(out[:, -1, :]))  # (B, vocab_size)
        return logits


# ── Entrenamiento ──────────────────────────────────────────────────────────────

def entrenar():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}")

    # 1. Datos
    frases = leer_corpus()
    vocab, idx = construir_vocab(frases)
    X, Y = generar_pares(frases, idx)

    dataset = PredDataset(X, Y)
    n_test  = int(len(dataset) * TEST_SPLIT)
    n_train = len(dataset) - n_test
    train_ds, test_ds = random_split(dataset, [n_train, n_test],
                                     generator=torch.Generator().manual_seed(SEED))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE)
    print(f"Train: {n_train:,} | Test: {n_test:,}")

    # 2. Modelo
    model = ModeloLSTM(len(vocab), EMB_DIM, HIDDEN_DIM, N_CAPAS, DROPOUT).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Parámetros del modelo: {n_params:,}")

    criterion = nn.CrossEntropyLoss(ignore_index=0)  # ignora PAD
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=LR, steps_per_epoch=len(train_loader), epochs=EPOCHS
    )

    # 3. Loop de entrenamiento
    print("\n── Entrenamiento ──")
    historial = {"train_loss": [], "test_loss": [], "test_acc_top1": [], "test_acc_top3": []}

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        model.train()
        total_loss = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()
        train_loss = total_loss / len(train_loader)

        # Evaluación en test
        model.eval()
        test_loss = 0
        correct_top1 = 0
        correct_top3 = 0
        total = 0
        with torch.no_grad():
            for xb, yb in test_loader:
                xb, yb = xb.to(device), yb.to(device)
                logits = model(xb)
                loss = criterion(logits, yb)
                test_loss += loss.item()
                # accuracy top-1
                pred1 = logits.argmax(dim=1)
                correct_top1 += (pred1 == yb).sum().item()
                # accuracy top-3
                top3 = logits.topk(3, dim=1).indices
                correct_top3 += sum(yb[i] in top3[i] for i in range(len(yb)))
                total += len(yb)

        test_loss /= len(test_loader)
        acc1 = correct_top1 / total * 100
        acc3 = correct_top3 / total * 100
        elapsed = time.time() - t0

        historial["train_loss"].append(round(train_loss, 4))
        historial["test_loss"].append(round(test_loss, 4))
        historial["test_acc_top1"].append(round(acc1, 2))
        historial["test_acc_top3"].append(round(acc3, 2))

        print(f"Epoch {epoch:2d}/{EPOCHS} | "
              f"train_loss={train_loss:.4f} | test_loss={test_loss:.4f} | "
              f"acc_top1={acc1:.1f}% | acc_top3={acc3:.1f}% | {elapsed:.0f}s")

    print("\n── Métricas finales ──")
    print(f"Test loss:     {historial['test_loss'][-1]}")
    print(f"Accuracy top-1: {historial['test_acc_top1'][-1]}%")
    print(f"Accuracy top-3: {historial['test_acc_top3'][-1]}%")

    return model, vocab, idx, historial, device


# ── Exportar a numpy ───────────────────────────────────────────────────────────

def exportar(model, vocab, idx, historial):
    """Convierte los pesos de PyTorch a numpy — igual que el corrector."""
    pesos = {k: v.cpu().numpy() for k, v in model.state_dict().items()}
    np.savez_compressed(SALIDA_NPZ, **pesos)

    config = {
        "vocab": vocab,
        "contexto": CONTEXTO,
        "emb_dim": EMB_DIM,
        "hidden_dim": HIDDEN_DIM,
        "n_capas": N_CAPAS,
        "historial_entrenamiento": historial,
    }
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\nModelo guardado en:")
    print(f"  {SALIDA_NPZ}")
    print(f"  {SALIDA_JSON}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model, vocab, idx, historial, device = entrenar()
    exportar(model, vocab, idx, historial)
    print("\nListo.")
