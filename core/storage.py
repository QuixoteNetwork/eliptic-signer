from __future__ import annotations

from pathlib import Path

# Detectar si es Android
try:
    from android.storage import app_storage_path
except ImportError:
    app_storage_path = None


def get_app_dir() -> Path:
    """
    Devuelve la ruta base segun plataforma.
    """
    if app_storage_path is not None:
        # Android → carpeta privada de la app
        return Path(app_storage_path())
    else:
        # Windows / Linux / macOS → como ya lo tenías
        return Path.home() / ".elipticsigner"


# Rutas
APP_DIR = get_app_dir()
KEYS_DIR = APP_DIR / "keys"
CONTACTS_FILE = APP_DIR / "contacts.json"
MY_PRIVATE_KEY_FILE = KEYS_DIR / "my_private_key.pem"
MY_PUBLIC_KEY_FILE = KEYS_DIR / "my_public_key.pem"


def ensure_app_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_DIR.mkdir(parents=True, exist_ok=True)