import os
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv
load_dotenv()


# ========== CONFIGURACIÓN ==========
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("❌ Falta la variable de entorno SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


# ========== FUNCIONES JWT ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ========== FUNCIONES BCRYPT ==========
def get_password_hash(password: str) -> str:
    """Genera hash de la contraseña con protección para contraseñas largas."""
    if len(password.encode("utf-8")) > 72:
        intermediate_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return bcrypt.hashpw(
            intermediate_hash.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña, compatible con ambos métodos de hash."""
    try:
        if bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        ):
            return True
    except Exception:
        pass

    try:
        intermediate_hash = hashlib.sha256(
            plain_password.encode("utf-8")
        ).hexdigest()
        return bcrypt.checkpw(
            intermediate_hash.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False