import os
from pathlib import Path

# Directorios
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Crea el directorio si no existe

# Configuración de archivos
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'image/jpg'
}

# Configuración de la aplicación
APP_CONFIG = {
    "upload_dir": str(UPLOAD_DIR),
    "max_file_size": MAX_FILE_SIZE,
    "allowed_extensions": ALLOWED_EXTENSIONS,
    "allowed_mime_types": ALLOWED_MIME_TYPES,
    "avatar_base_url": "/uploads/avatars/"  # URL base para servir archivos
}