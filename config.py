# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === já existia algo assim ===
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
DATA_DIR = os.path.join(BASE_DIR, "data")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")

# === NOVO: configs de Flask/DB ===
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")  # troque em produção

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Pasta para avatares
AVATAR_UPLOAD_FOLDER = os.path.join("static", "avatars")
ALLOWED_AVATAR_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}