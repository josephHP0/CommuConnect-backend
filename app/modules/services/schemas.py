from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

from app.core.enums import ModalidadServicio

class ServicioResumen(BaseModel):
    nombre: str
    modalidad: str
    class Config:
        orm_mode = True

class ServicioOut(BaseModel):
    id_servicio: int
    nombre: str
    modalidad: str
    descripcion: Optional[str] = None
    imagen: Optional[str] = None  # base64


class ProfesionalRead(BaseModel):
    id_profesional: int
    nombre_completo: Optional[str]
    id_servicio: Optional[int]
    formulario: Optional[str]
    fecha_creacion: Optional[datetime]
    creado_por: Optional[str]
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: Optional[bool]

    model_config = ConfigDict(from_attributes=True)


class DistritoOut(BaseModel):
    id_distrito: int
    nombre: str
    imagen: Optional[str] = None  # base64

class LocalOut(BaseModel):
    id_local: int
    nombre: Optional[str]
    direccion_detallada: Optional[str]
    responsable: Optional[str]
    link: Optional[str]

    class Config:
        orm_mode = True


class ServicioRead(BaseModel):
    id_servicio: int
    nombre: str
    descripcion: str
    modalidad: str
    imagen_base64: Optional[str]
    fecha_creacion: Optional[datetime]
    creado_por: Optional[str]
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: bool

    class Config:
        orm_mode = True

class ServicioCreate(BaseModel):
    nombre: str
    descripcion: str
    modalidad: ModalidadServicio

class ServicioUpdate(BaseModel):
    nombre: Optional[str]
    descripcion: Optional[str]
    modalidad: Optional[ModalidadServicio]  # Ya definido antes