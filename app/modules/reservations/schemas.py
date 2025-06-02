from typing import List
from datetime import date
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

    class Config:
        # En este caso, solo devolvemos cadenas. No necesitamos json_encoders para date.
        orm_mode = True