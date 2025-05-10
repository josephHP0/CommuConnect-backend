from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Usuario(SQLModel, table=True):
    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=60)
    apellido: str = Field(max_length=60)
    email: str = Field(max_length=60, unique=True, index=True)
    password: str = Field(max_length=60)
    fecha_creacion: Optional[datetime] = None
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[bool] = True
