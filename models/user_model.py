from sqlalchemy import Boolean, Column, String, LargeBinary, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    username = Column(String(50), primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    
    # Nuevos campos obligatorios
    phone_number = Column(String(20), nullable=False)
    id_number = Column(String(50), nullable=False)
    
    # Nuevos campos opcionales
    address = Column(String(200), nullable=True)
    avatar = Column(LargeBinary, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    avatar_filename = Column(String(255), nullable=True)  # Nombre del archivo local
    avatar_mime_type = Column(String(50), nullable=True)  # Tipo MIME (image/jpeg, etc.)
    
    # Campos de auditoría
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "id_number": self.id_number,
            "address": self.address,
            "avatar_url": self.avatar_url,
            "has_avatar": bool(self.avatar or self.avatar_url),
            "avatar_mime_type": self.avatar_mime_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
'''class User(Base):
    __tablename__ = "users"
    
    username = Column(String(50), primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active
        }'''