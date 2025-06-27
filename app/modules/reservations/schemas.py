from typing import List, Optional
from datetime import date, time, datetime
from pydantic import BaseModel, ConfigDict
from app.modules.reservations.models   import Sesion, Reserva, SesionVirtual


class FechasPresencialesResponse(BaseModel):
    fechas: List[date]
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={date: lambda d: d.strftime("%d/%m/%Y")}
    )

class HorasPresencialesResponse(BaseModel):
    horas: List[str]


class SesionPresencialOut(BaseModel):
    id_sesion: int
    id_sesion_presencial: int
    fecha: date
    ubicacion: str           # Ejemplo: "La Tiendita (San Miguel)"
    responsable: Optional[str] = None
    hora_inicio: str
    hora_fin: str
    vacantes_totales: Optional[int] = None
    vacantes_libres: int
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={date: lambda d: d.strftime("%d/%m/%Y")}
    )


class ListaSesionesPresencialesResponse(BaseModel):
    sesiones: List[SesionPresencialOut]
    model_config = ConfigDict(from_attributes=True)

class ReservaCreate(BaseModel):
    id_sesion: int  # ID de la sesión virtual a reservar
    id_comunidad: int  

class ReservaRequest(BaseModel):
    id_sesion: int

class ReservaResponse(BaseModel):
    id_reserva: int
    id_sesion: int
    id_cliente: int
    id_comunidad: Optional[int] = None
    estado_reserva: str
    fecha_reservada: Optional[datetime]
    url_archivo: Optional[str]
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)

class ReservaPresencialCreadaResponse(BaseModel):
    id_reserva: int
    nombre_servicio: str
    fecha: Optional[date]
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    ubicacion: Optional[str]
    direccion_detallada: Optional[str]
    nombre_cliente: str
    apellido_cliente: str
    topes_disponibles: Optional[int]
    topes_consumidos: Optional[int]

class FormularioInfoResponse(BaseModel):
    profesional_nombre: str
    fecha_sesion: date
    hora_inicio: time
    hora_fin: time
    url_formulario: Optional[str] = None
    formulario_completado: bool

class ReservaPresencialSummary(SesionPresencialOut):
    nombres: str
    apellidos: str
    vacantes_libres: Optional[int] = None

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
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            date: lambda v: v.strftime('%d/%m/%Y'),
            time: lambda v: v.strftime('%H:%M'),
        }
    )

class ListaReservasResponse(BaseModel):
    reservas: List[ReservaDetailResponse]
    model_config = ConfigDict(from_attributes=True)

class ReservaComunidadResponse(BaseModel):
    id_reserva: int
    nombre_servicio: str
    fecha: date
    hora_inicio: time
    hora_fin: time
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            date: lambda v: v.strftime('%d/%m/%Y'),
            time: lambda v: v.strftime('%H:%M'),
        }
    )

class ListaReservasComunidadResponse(BaseModel):
    reservas: List[ReservaComunidadResponse]
    model_config = ConfigDict(from_attributes=True)

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
    reserva_pasada: bool
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            date: lambda v: v.strftime('%d/%m/%Y') if v else None,
            time: lambda v: v.strftime('%H:%M') if v else None,
        }
    )
