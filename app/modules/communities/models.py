from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Comunidad(SQLModel, table=True):
    id_comunidad: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    slogan: Optional[str] = Field(default=None, max_length=350)
    imagen: Optional[bytes] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = Field(default=None)
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: bool = Field(default=True)
