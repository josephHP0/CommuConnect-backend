from typing import List, Optional
from datetime import date,time
from pydantic import BaseModel
from datetime import datetime

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
    vacantes_totales: int
    vacantes_libres: int

    class Config:
        orm_mode = True


class ListaSesionesPresencialesResponse(BaseModel):
    sesiones: List[SesionPresencialOut]

    class Config:
        orm_mode = True

class ReservaCreate(BaseModel):
    id_sesion: int  # ID de la sesión virtual a reservar

class ReservaOut(BaseModel):
    """
    Schema para la respuesta de una reserva.
    Incluye datos básicos y, en caso de sesión virtual, la URL asociada.
    """
    id_reserva: int
    id_sesion: int
    id_cliente: int
    estado_reserva: str
    fecha_reserva: datetime
    url_archivo: Optional[str]

    class Config:
        orm_mode = True
