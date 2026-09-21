import bcrypt
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# ========== CONFIGURACIÓN ==========
SECRET_KEY = "my-secret-key-change-in-production"  # ¡Cambiar en producción!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ========== FUNCIONES JWT ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ========== FUNCIONES BCRYPT ==========
def get_password_hash(password: str) -> str:
    """
    Genera hash de la contraseña con protección automática 
    para contraseñas largas (>72 bytes).
    """
    # Si la contraseña es muy larga, usamos un hash intermedio SHA-256
    if len(password.encode('utf-8')) > 72:
        # Paso 1: Hash con SHA-256 para normalizar a 64 bytes
        intermediate_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        # Paso 2: Aplicar bcrypt al hash SHA-256
        return bcrypt.hashpw(
            intermediate_hash.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
    else:
        # Contraseña normal, bcrypt directo
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica contraseña, compatible con ambos métodos de hash.
    """
    try:
        # Intento 1: Verificación directa (para contraseñas normales)
        if bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
    except:
        pass
    
    # Intento 2: Si falla, probar con método SHA-256 + bcrypt
    try:
        intermediate_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return bcrypt.checkpw(
            intermediate_hash.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except:
        return False