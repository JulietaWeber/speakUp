import gdown
import os

if not os.path.exists("SBW-vectors-300-min5.txt"):
    print("Descargando embeddings desde Google Drive...")
    gdown.download(
        "https://drive.google.com/uc?id=1OCxLvjew9V-UMU0RLV-DcEfKd3Tu8oY6",
        "SBW-vectors-300-min5.txt",
        quiet=False
    )
    print("Embeddings descargados")
else:
    print("Embeddings ya existen, no se descargan")