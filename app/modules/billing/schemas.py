from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from typing import Union

class PlanOut(BaseModel):
    id_plan: int
    titulo: str
    descripcion: str
    topes: Union[int, str]
    precio: float

    @property
    def topes_display(self):
        return "ilimitado" if isinstance(self.topes, int) and self.topes > 100 else self.topes

    class Config:
        from_attributes = True  # <--- Cambia esto

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["topes"] = self.topes_display
        return data


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