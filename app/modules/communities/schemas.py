import base64
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, validator
from app.modules.services.schemas import ServicioResumen
from typing import List, Optional
from app.modules.services.schemas import ServicioOut
from utils.datetime_utils import convert_utc_to_local

class ComunidadCreate(BaseModel):
    nombre: str
    slogan: Optional[str]
    imagen: Optional[bytes]
    creado_por: str

class ComunidadRead(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str] = None
    imagen: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    creado_por: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = None
    estado: int 

    @validator('fecha_creacion', 'fecha_modificacion', pre=True, always=True)
    def localize_dates(cls, v):
        if v:
            return convert_utc_to_local(v)
        return v

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
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = None
    estado: int

    @validator('fecha_creacion', 'fecha_modificacion', pre=True, always=True)
    def localize_dates(cls, v):
        if v:
            return convert_utc_to_local(v)
        return v

    model_config = ConfigDict(from_attributes=True)

class ComunidadContexto(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str] = None
    imagen: Optional[str] = None  # Codificada en base64 para frontend
    servicios: Optional[List[ServicioResumen]] = [] 
    estado_membresia: Optional[bool] = None  # True si tiene membresía activa
    estado_inscripcion: Optional[int] = None  # 1 = activo, 0 = inactivo, None = no inscrito

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_base64(cls, comunidad, servicios=None, estado_membresia=None, estado_inscripcion=None):
        data = comunidad.__dict__.copy()
        if comunidad.imagen:
            data["imagen"] = base64.b64encode(comunidad.imagen).decode("utf-8")
        if servicios is not None:
            data["servicios"] = servicios
        data["estado_membresia"] = estado_membresia
        data["estado_inscripcion"] = estado_inscripcion
        return cls(**data)

class ComunidadDetalleOut(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str] = None  # Aquí se usará como descripción
    imagen: Optional[str] = None  # base64
    servicios: List[ServicioOut]