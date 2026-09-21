from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, HttpUrl
from typing import Optional, Union, Any
from datetime import datetime
import re
from fastapi import UploadFile, File
import os

# Base común
class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: str
    id_number: str

# Para creación de usuario (sin archivo en el request)
class UserCreate(UserBase):
    password: str
    address: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None  # URL validada
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        clean_phone = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[1-9]\d{7,14}$', clean_phone):
            raise ValueError('Número de teléfono inválido')
        return clean_phone
    
    @field_validator('id_number')
    @classmethod
    def validate_id_number(cls, v: str) -> str:
        if len(v) < 4 or len(v) > 20:
            raise ValueError('El número de identificación debe tener entre 4 y 20 caracteres')
        return v.upper()

# Para subir avatar
class AvatarUpload(BaseModel):
    avatar: UploadFile

# Para actualización de usuario
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return UserCreate.validate_phone_number(v)
    
    @field_validator('id_number')
    @classmethod
    def validate_id_number_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return UserCreate.validate_id_number(v)

# Para respuesta pública - VERSIÓN CORREGIDA
class UserPublic(UserBase):
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_filename: Optional[str] = None  # Añadido campo faltante
    avatar_mime_type: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None  # Cambiado a datetime
    updated_at: Optional[datetime] = None  # Añadido campo de actualización
    has_avatar: bool = False
    
    @field_validator('has_avatar', mode='before')
    @classmethod
    def set_has_avatar(cls, v, info):
        """Determina si el usuario tiene avatar basado en otros campos"""
        data = info.data
        return bool(data.get('avatar_url') or data.get('avatar_filename'))
    
    # Validador para convertir created_at a string si es necesario
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def datetime_to_str(cls, v):
        """Convierte datetime a string ISO format si es datetime"""
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Configuración global para serializar datetime
            datetime: lambda v: v.isoformat() if v else None
        }
    )

# Versión alternativa si prefieres que created_at sea string directamente
class UserPublicSimple(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: str
    id_number: str
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_filename: Optional[str] = None
    avatar_mime_type: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None  # String directamente
    updated_at: Optional[str] = None  # String directamente
    has_avatar: bool = False
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def ensure_string(cls, v):
        """Asegura que las fechas sean strings"""
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    @field_validator('has_avatar', mode='before')
    @classmethod
    def set_has_avatar(cls, v, info):
        data = info.data
        return bool(data.get('avatar_url') or data.get('avatar_filename'))
    
    model_config = ConfigDict(from_attributes=True)

# Para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    
    

'''# Base común
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

# Para creación de usuario
class UserCreate(UserBase):
    password: str

# Para actualización de usuario
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

# Para respuesta pública (sin password) - FIXED
class UserPublic(UserBase):
    is_active: bool = True
    
    # Modern Pydantic V2 configuration
    model_config = ConfigDict(from_attributes=True)

# Para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None'''