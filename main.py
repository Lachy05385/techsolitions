from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.templating import Jinja2Templates
import shutil
import os
from pathlib import Path
import tempfile

# Importaciones propias
from database import get_db, engine, SessionLocal
from models.user_model import Base, User
from schemas.user_schema import Token, UserPublic, UserCreate, UserUpdate
from security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token
)

# ========== CONFIGURACIÓN DE AVATARES ==========
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de archivos
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'image/jpg'
}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# ========== DEPENDENCIAS ==========
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene el usuario actual desde el token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username = payload.get("username")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Verifica que el usuario esté activo"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# ========== APLICACIÓN ==========
app = FastAPI(title="User Management API with Avatars")
templates = Jinja2Templates(directory="templates")

# Servir archivos estáticos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ========== STARTUP EVENT ==========
@app.on_event("startup")
def startup_event():
    """Inserta usuarios de ejemplo al iniciar la aplicación"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existen usuarios
        existing_users = db.query(User).count()
        
        if existing_users == 0:
            # Crear usuarios de ejemplo
            users_data = [
                User(
                    username="pedro",
                    email="pedro@gmail.com",
                    password=get_password_hash("Admin123!"),
                    full_name="Pedro Pérez",
                    phone_number="+34600123456",
                    id_number="12345678A",
                    address="Calle Mayor 123, Madrid",
                    avatar_url="https://i.pravatar.cc/150?img=1",
                    is_active=True
                ),
                User(
                    username="juan",
                    email="juan@gmail.com",
                    password=get_password_hash("admin321"),
                    full_name="Juan García",
                    phone_number="+34600234567",
                    id_number="87654321B",
                    is_active=True
                )
            ]
            
            db.add_all(users_data)
            db.commit()
            print("✅ Usuarios de ejemplo creados exitosamente")
        else:
            print("✅ Base de datos ya contiene usuarios")
            
    except Exception as e:
        print(f"❌ Error al inicializar datos: {e}")
        db.rollback()
    finally:
        db.close()

@app.get("/index", include_in_schema=False)
async def portafolio():
    return FileResponse("templates/index.html")
        
        
@app.get("/portafolio", include_in_schema=False)
async def portafolio():
    return FileResponse("templates/portafolio.html")




# ========== ENDPOINTS DE AUTENTICACIÓN ==========
@app.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint para autenticación"""
    # Validar longitud de contraseña antes de procesar
    if len(form_data.password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales inválidas"
        )
    
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario o contraseña incorrectos"
        )
    
    token_data = {"username": user.username, "email": user.email}
    access_token = create_access_token(data=token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}

# ========== ENDPOINTS DE USUARIOS ==========
@app.post("/users/", response_model=UserPublic)
def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    phone_number: str = Form(...),
    id_number: str = Form(...),
    address: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario con opción de avatar"""
    
    # Verificar si el usuario ya existe
    db_user = db.query(User).filter(
        (User.username == username) | 
        (User.email == email) |
        (User.id_number == id_number)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email or ID number already registered"
        )
    
    try:
        # Crear usuario básico
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            full_name=full_name,
            phone_number=phone_number,
            id_number=id_number,
            address=address,
            avatar_url=avatar_url
        )
        
        # Procesar avatar si se proporciona archivo
        if avatar_file and avatar_file.filename:
            # Validar tipo MIME
            if avatar_file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tipo de archivo no permitido. Permitidos: {', '.join(ALLOWED_MIME_TYPES)}"
                )
            
            # Validar tamaño
            file_size = 0
            if hasattr(avatar_file.file, 'seek') and hasattr(avatar_file.file, 'tell'):
                avatar_file.file.seek(0, 2)
                file_size = avatar_file.file.tell()
                avatar_file.file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            # Generar nombre de archivo seguro
            file_extension = Path(avatar_file.filename).suffix.lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                file_extension = ".jpg"
            
            safe_filename = f"{username}_{os.urandom(4).hex()}{file_extension}"
            file_path = UPLOAD_DIR / safe_filename
            
            # Guardar archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(avatar_file.file, buffer)
            
            # Leer para BD (opcional)
            with open(file_path, "rb") as f:
                new_user.avatar = f.read()
            
            new_user.avatar_filename = safe_filename
            new_user.avatar_mime_type = avatar_file.content_type
            if not avatar_url:  # Si no hay URL externa, usar la local
                new_user.avatar_url = f"/uploads/avatars/{safe_filename}"
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.get("/users/profile", response_model=UserPublic)
def get_profile(current_user: User = Depends(get_current_active_user)):
    """Obtiene el perfil del usuario actual"""
    # Asegurar que updated_at esté presente
    if not hasattr(current_user, 'updated_at'):
        current_user.updated_at = None
    return current_user

@app.get("/users/", response_model=List[UserPublic])
def get_all_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene todos los usuarios (requiere autenticación)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{username}", response_model=UserPublic)
def get_user(
    username: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene un usuario específico por username"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@app.put("/users/{username}", response_model=UserPublic)
def update_user(
    username: str,
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    id_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza un usuario"""
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Actualizar campos
    update_fields = {
        "full_name": full_name,
        "email": email,
        "phone_number": phone_number,
        "id_number": id_number,
        "address": address,
        "is_active": is_active
    }
    
    for field, value in update_fields.items():
        if value is not None:
            setattr(user, field, value)
    
    # Actualizar contraseña si se proporciona
    if password:
        user.password = get_password_hash(password)
    
    db.commit()
    db.refresh(user)
    
    return user

# ========== ENDPOINTS DE AVATAR ==========
@app.post("/users/{username}/avatar/upload", response_model=UserPublic)
async def upload_avatar(
    username: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sube un avatar para el usuario"""
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para actualizar este usuario"
        )
    
    # Validar archivo
    if not file.content_type in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Permitidos: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Validar tamaño
    file_size = 0
    if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generar nombre de archivo seguro
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        file_extension = ".jpg"
    
    safe_filename = f"{username}_{os.urandom(4).hex()}{file_extension}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Leer archivo para guardar en BD (opcional)
        with open(file_path, "rb") as f:
            avatar_data = f.read()
        
        # Actualizar usuario en BD
        user = db.query(User).filter(User.username == username).first()
        if user:
            # Eliminar archivo anterior si existe
            if user.avatar_filename:
                old_file_path = UPLOAD_DIR / user.avatar_filename
                if old_file_path.exists():
                    old_file_path.unlink()
            
            user.avatar = avatar_data
            user.avatar_filename = safe_filename
            user.avatar_mime_type = file.content_type
            user.avatar_url = f"/uploads/avatars/{safe_filename}"
            
            db.commit()
            db.refresh(user)
            
            return user
        else:
            # Limpiar archivo si el usuario no existe
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
    except Exception as e:
        # Limpiar en caso de error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo archivo: {str(e)}"
        )

@app.post("/users/{username}/avatar/url", response_model=UserPublic)
def set_avatar_from_url(
    username: str,
    avatar_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Establece el avatar desde una URL externa"""
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para actualizar este usuario"
        )
    
    # Validar URL
    if not avatar_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL inválida"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Eliminar archivo anterior si existe
    if user.avatar_filename:
        old_file_path = UPLOAD_DIR / user.avatar_filename
        if old_file_path.exists():
            old_file_path.unlink()
    
    # Actualizar
    user.avatar_url = avatar_url
    user.avatar = None
    user.avatar_filename = None
    user.avatar_mime_type = None
    
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/users/{username}/avatar", response_model=UserPublic)
def delete_avatar(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Elimina el avatar del usuario"""
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para actualizar este usuario"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Eliminar archivo local si existe
    if user.avatar_filename:
        file_path = UPLOAD_DIR / user.avatar_filename
        if file_path.exists():
            file_path.unlink()
    
    # Limpiar campos en BD
    user.avatar = None
    user.avatar_filename = None
    user.avatar_mime_type = None
    user.avatar_url = None
    
    db.commit()
    db.refresh(user)
    
    return user

@app.get("/users/{username}/avatar")
def get_avatar(
    username: str,
    db: Session = Depends(get_db)
):
    """Obtiene el avatar del usuario (devuelve la imagen)"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Si hay archivo local
    if user.avatar_filename:
        file_path = UPLOAD_DIR / user.avatar_filename
        if file_path.exists():
            return FileResponse(
                path=file_path,
                media_type=user.avatar_mime_type or "image/jpeg",
                filename=f"avatar_{username}{Path(user.avatar_filename).suffix}"
            )
    
    # Si hay avatar en BD (binario)
    if user.avatar:
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(user.avatar)
        temp_file.close()
        
        # Usar FileResponse temporal
        response = FileResponse(
            path=temp_file.name,
            media_type=user.avatar_mime_type or "image/jpeg",
            filename=f"avatar_{username}.jpg"
        )
        
        # Configurar callback para eliminar archivo temporal
        response.background = BackgroundTasks()
        response.background.add_task(lambda: os.unlink(temp_file.name))
        return response
    
    # Si hay URL pero no archivo local
    if user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Avatar disponible en: {user.avatar_url}",
            headers={"Location": user.avatar_url}
        )
    
    # Si no hay avatar, devolver uno por defecto o 404
    default_avatar = Path("static/default-avatar.jpg")
    if default_avatar.exists():
        return FileResponse(
            path=default_avatar,
            media_type="image/jpeg",
            filename=f"default_avatar.jpg"
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no tiene avatar"
    )

# ========== ENDPOINT RAÍZ ==========
@app.get("/")
def read_root():
    return {
        "message": "User Management API with Avatar Support",
        "endpoints": {
            "auth": {
                "login": "POST /auth/login",
                "profile": "GET /users/profile"
            },
            "users": {
                "create_user": "POST /users/",
                "get_all_users": "GET /users/",
                "get_user": "GET /users/{username}",
                "update_user": "PUT /users/{username}"
            },
            "avatars": {
                "upload_avatar": "POST /users/{username}/avatar/upload",
                "set_avatar_url": "POST /users/{username}/avatar/url",
                "delete_avatar": "DELETE /users/{username}/avatar",
                "get_avatar": "GET /users/{username}/avatar"
            }
        }
    }

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)