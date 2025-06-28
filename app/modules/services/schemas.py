from pydantic import BaseModel, validator
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

from app.core.enums import ModalidadServicio
from utils.datetime_utils import convert_utc_to_local
from datetime import date, time

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
    email: Optional[str]  # <-- Añade este campo

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
    descripcion: Optional[str]
    modalidad: Optional[str]
    imagen_base64: Optional[str]
    fecha_creacion: Optional[datetime]
    creado_por: Optional[str]
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: Optional[bool]

    @validator('fecha_creacion', 'fecha_modificacion', pre=True, always=True)
    def localize_dates(cls, v):
        if v:
            return convert_utc_to_local(v)
        return v

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

class LocalOut(BaseModel):
    id_local: int
    nombre: str
    direccion_detallada: Optional[str]
    link: Optional[str]
    responsable: Optional[str]

class ProfesionalOut(BaseModel):
    id_profesional: int
    nombre_completo: Optional[str]
    email: Optional[str]
    id_servicio: Optional[int]
    formulario: Optional[str]

class ProfesionalCreate(BaseModel):
    nombre_completo: Optional[str]
    email: Optional[str]
    id_servicio: Optional[int]
    formulario: Optional[str]

class SesionVirtualConDetalle(BaseModel):
    id_sesion_virtual: int
    id_sesion: int
    fecha: Optional[date]
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    inscritos: int

    class Config:
        from_attributes = True  

class ProfesionalDetalleOut(BaseModel):
    nombre: str
    apellido: str
    email: Optional[str]


class InscritoDetalleOut(BaseModel):
    nombre: str
    apellido: str
    comunidad: str
    entrego_archivo: bool


class DetalleSesionVirtualResponse(BaseModel):
    id_sesion_virtual: int
    descripcion: Optional[str]
    fecha: Optional[date]
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    profesional: ProfesionalDetalleOut
    inscritos: List[InscritoDetalleOut]
