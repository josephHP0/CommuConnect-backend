from datetime import datetime
from pydantic import BaseModel, validator
from typing import Optional, Union
from utils.datetime_utils import convert_utc_to_local

class PlanOut(BaseModel):
    id_plan: int
    titulo: str
    duracion: Optional[int] = None
    descripcion: str
    topes: Optional[Union[int, str]] = None
    precio: float
    estado: int 

    @validator("topes", pre=True, always=True)
    def mostrar_ilimitado_si_none(cls, v):
        return "ilimitado" if v is None else v

    class Config:
        from_attributes = True


class UsoTopesOut(BaseModel):
    plan: Optional[str] = None
    topes_disponibles: Optional[int] = None
    topes_consumidos: Optional[int] = None
    estado: str

class DetalleInscripcionBase(BaseModel):
    id_inscripcion: int
    fecha_registro: datetime
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    topes_disponibles: Optional[int] = None
    topes_consumidos: int
    estado: int

class DetalleInscripcionCreate(DetalleInscripcionBase):
    creado_por: str

class DetalleInscripcionOut(DetalleInscripcionBase):
    id_registros_inscripcion: int
    fecha_creacion: datetime
    creado_por: str
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = None

    @validator('fecha_registro', 'fecha_inicio', 'fecha_fin', 'fecha_creacion', 'fecha_modificacion', pre=True, always=True)
    def localize_dates(cls, v):
        if v:
            return convert_utc_to_local(v)
        return v

    class Config:
        orm_mode = True


class MembresiaAsociadaOut(BaseModel):
    tieneMembresiaAsociada: bool

    class Config:
        orm_mode = True

class ValidacionMembresiaOut(BaseModel):
    tieneMembresiaActiva: bool

class TieneTopesOut(BaseModel):
    tieneTopes: bool

class EsPlanConTopesOut(BaseModel):
    esPlanConTopes: bool

class InfoInscripcionOut(BaseModel):
    id_inscripcion: int
    estado: int
    titulo: str
    descripcion_plan: str
    precio: float
    periodo: str
    fecha_fin: Optional[str]
    fecha_inicio: Optional[str]
    topes_disponibles: Optional[Union[int, str]]

    @validator('fecha_inicio', 'fecha_fin', pre=True, always=True)
    def format_and_localize_dates(cls, v):
        if isinstance(v, datetime):
            local_dt = convert_utc_to_local(v)
            return local_dt.isoformat() if local_dt else None
        return v # Mantiene el valor si ya es string o None
    

class ComunidadXPlanCreate(BaseModel):
    id_comunidad: int
    id_plan: int

class InscripcionResumenOut(BaseModel):
    id_inscripcion: int
    fecha_inicio: Optional[str]
    titulo_plan: str
    precio: float

class DetalleInscripcionPagoOut(BaseModel):
    nombre_membresia: str
    fecha_pago: Optional[str]
    hora_pago: Optional[str]
    id_pago: Optional[int]
    tarjeta: str

class SuspensionEstadoOut(BaseModel):
    id_suspension: int
    id_cliente: int
    id_inscripcion: int
    motivo: str
    fecha_inicio: str
    fecha_fin: str
    estado: str

class PlanCreate(BaseModel):
    titulo: str
    descripcion: str
    duracion: Optional[int] = None
    topes: Optional[int] = None
    precio: float

class PlanUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    duracion: Optional[int] = None
    topes: Optional[int] = None
    precio: Optional[float] = None