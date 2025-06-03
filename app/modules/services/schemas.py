from pydantic import BaseModel
from typing import Optional

class ServicioResumen(BaseModel):
    nombre: str

    class Config:
        orm_mode = True


class ServicioOut(BaseModel):
    id_servicio: int
    nombre: str
    descripcion: Optional[str] = None
    imagen: Optional[str] = None  # base64