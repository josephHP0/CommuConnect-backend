from typing import List
from datetime import date,time
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
    fecha: date
    ubicacion: str           # Ejemplo: "La Tiendita (San Miguel)"
    responsable: str         # El campo creado_por de SesionPresencial o de Sesion
    hora_inicio: time
    hora_fin: time
    vacantes_totales: int
    vacantes_libres: int

    class Config:
        orm_mode = True


class ListaSesionesPresencialesResponse(BaseModel):
    sesiones: List[SesionPresencialOut]

    class Config:
        orm_mode = True