from typing import List, Optional
from datetime import date, time, datetime
from pydantic import BaseModel

class FechasPresencialesResponse(BaseModel):
    fechas: List[date]

    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda d: d.strftime("%d/%m/%Y")
        }

class HorasPresencialesResponse(BaseModel):
    horas: List[str]


class SesionPresencialOut(BaseModel):
    id_sesion: int
    id_sesion_presencial: int
    fecha: date
    ubicacion: str           # Ejemplo: "La Tiendita (San Miguel)"
    responsable: Optional[str]         # El campo creado_por de SesionPresencial o de Sesion
    hora_inicio: str
    hora_fin: str
    vacantes_totales: Optional[int] = None
    vacantes_libres: int

    class Config:
        orm_mode = True


class ListaSesionesPresencialesResponse(BaseModel):
    sesiones: List[SesionPresencialOut]

    class Config:
        orm_mode = True

class ReservaPresencialSummary(SesionPresencialOut):
    nombres: str
    apellidos: str
    vacantes_libres: Optional[int] = None

class ReservaRequest(BaseModel):
    id_sesion: int

class ReservaResponse(BaseModel):
    id_reserva: int
    id_sesion: int
    id_cliente: int
    estado_reserva: str
    fecha_creacion: datetime

    class Config:
        orm_mode = True

class ReservaDetailResponse(BaseModel):
    id_reserva: int
    nombre_servicio: str
    fecha: date
    hora_inicio: time
    hora_fin: time
    ubicacion: str
    direccion_detallada: Optional[str] = None
    nombre_cliente: str
    apellido_cliente: str
    topes_disponibles: Optional[int] = None
    topes_consumidos: Optional[int] = None

    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda v: v.strftime('%d/%m/%Y'),
            time: lambda v: v.strftime('%H:%M'),
        }