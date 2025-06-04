import base64
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.modules.services.schemas import ServicioResumen
from typing import List, Optional


class ComunidadCreate(BaseModel):
    nombre: str
    slogan: Optional[str]
    imagen: Optional[bytes]
    creado_por: str

class ComunidadRead(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str]
    imagen: Optional[str] = None
    fecha_creacion: datetime
    creado_por: str
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: bool
    class Config:
        orm_mode = True
    @classmethod
    def from_orm_with_base64(cls, comunidad):
        data = comunidad.__dict__.copy()
        if comunidad.imagen:
            data["imagen"] = base64.b64encode(comunidad.imagen).decode("utf-8")
        return cls(**data)

class ComunidadOut(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str] = None
    imagen: Optional[str] = None
    fecha_creacion: datetime
    creado_por: str
    fecha_modificacion: Optional[datetime] = None  # <-- Permitir None
    modificado_por: Optional[str] = None           # <-- Permitir None
    estado: int

    model_config = ConfigDict(from_attributes=True)


class ComunidadContexto(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str] = None
    imagen: Optional[str] = None  # Codificada en base64 para frontend
    servicios: Optional[List[ServicioResumen]] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_base64(cls, comunidad, servicios=None):
        data = comunidad.__dict__.copy()
        if comunidad.imagen:
            data["imagen"] = base64.b64encode(comunidad.imagen).decode("utf-8")
        if servicios is not None:
            data["servicios"] = servicios
        return cls(**data)
    