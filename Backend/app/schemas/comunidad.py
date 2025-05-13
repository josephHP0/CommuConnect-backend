from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ComunidadCreate(BaseModel):
    nombre: str
    slogan: Optional[str]
    imagen: Optional[bytes]
    creado_por: str

class ComunidadRead(BaseModel):
    id_comunidad: int
    nombre: str
    slogan: Optional[str]
    imagen: Optional[bytes]
    fecha_creacion: datetime
    creado_por: str
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: bool
    