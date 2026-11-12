from pydantic import BaseModel, Field
from typing import List, Literal


class ModuloEstimado(BaseModel):
    nombre: str = Field(..., description="Nombre del módulo (ej. Backend, Base de Datos)")
    presente_en_descripcion: bool = Field(
        ..., description="Si el cliente lo mencionó explícitamente o no"
    )
    horas_min: int = Field(..., ge=0)
    horas_max: int = Field(..., ge=0)
    justificacion: str = Field(..., description="Por qué se estiman esas horas")


class EstimacionResponse(BaseModel):
    complejidad: Literal["BÁSICO", "MEDIO", "ALTO"]
    modulos: List[ModuloEstimado]
    precio_min_usd: float = Field(..., ge=0)
    precio_max_usd: float = Field(..., ge=0)
    advertencias: List[str] = Field(
        default_factory=list,
        description="Información faltante o ambigüedades en la descripción del cliente"
    )
    resumen_para_cliente: str = Field(
        ..., description="Explicación breve en lenguaje sencillo de por qué cuesta eso"
    )