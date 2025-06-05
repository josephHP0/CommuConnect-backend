from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class PlanOut(BaseModel):
    id_plan: int
    titulo: str
    descripcion: str
    topes: int
    precio: float


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
    topes_disponibles: int
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

    class Config:
        orm_mode = True