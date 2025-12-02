# config.py
import os

# Pasta base do projeto (onde está o app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta onde ficam as séries/filmes
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Pasta para arquivos de dados (progresso, etc.)
DATA_DIR = os.path.join(BASE_DIR, "data")

# Arquivo onde vamos salvar o "continuar assistindo"
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
