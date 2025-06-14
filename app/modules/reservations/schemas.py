from typing import List, Optional
from datetime import date, time, datetime
from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel, ConfigDict


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
        json_encoders = {
            date: lambda d: d.strftime("%d/%m/%Y")
        }


class ListaSesionesPresencialesResponse(BaseModel):
    sesiones: List[SesionPresencialOut]

    class Config:
        orm_mode = True

class ReservaCreate(BaseModel):
    id_sesion: int  # ID de la sesión virtual a reservar
    id_comunidad: int  

class ReservaOut(BaseModel):
    id_reserva: int
    id_sesion: int
    id_cliente: int
    id_comunidad: int
    estado_reserva: str
    fecha_reserva: Optional[datetime] = None
    url_archivo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2



class ReservaPresencialSummary(SesionPresencialOut):
    nombres: str
    apellidos: str
    vacantes_libres: Optional[int] = None

class ReservaRequest(BaseModel):
    id_sesion: int

class ReservaCreadaResponse(BaseModel):
    id_reserva: int
    id_sesion: int
    id_cliente: int
    estado_reserva: str
    fecha_reserva: datetime
    url_archivo: Optional[str]

    class Config:
        orm_mode = True
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

class ListaReservasResponse(BaseModel):
    reservas: List[ReservaDetailResponse]

    class Config:
        orm_mode = True

class ReservaComunidadResponse(BaseModel):
    id_reserva: int
    nombre_servicio: str
    fecha: date
    hora_inicio: time
    hora_fin: time

    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda v: v.strftime('%d/%m/%Y'),
            time: lambda v: v.strftime('%H:%M'),
        }

class ListaReservasComunidadResponse(BaseModel):
    reservas: List[ReservaComunidadResponse]

    class Config:
        orm_mode = True

class ReservaDetailScreenResponse(BaseModel):
    id_reserva: int
    nombre_servicio: str
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    tipo_sesion: str
    responsable: Optional[str] = None
    nombre_local: Optional[str] = None
    direccion: Optional[str] = None
    url_meeting: Optional[str] = None
    nombre_profesional: Optional[str] = None
    estado_reserva: str

    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda v: v.strftime('%d/%m/%Y'),
            time: lambda v: v.strftime('%H:%M'),
        }
