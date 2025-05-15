from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, TYPE_CHECKING
from app.core.enums import TipoUsuario
from sqlalchemy import Column, Enum as SQLEnum
from datetime import datetime
#if TYPE_CHECKING:
#from app.models.administrador import Administrador  # solo lo usará el type checker

#class Usuario(SQLModel, table=True):
   # id_usuario: Optional[int] = Field(default=None, primary_key=True)
   # nombre: str = Field(max_length=60)
   # apellido: str = Field(max_length=60)
    #email: str = Field(max_length=60, unique=True, index=True)
    #password: str = Field(max_length=60)
    #fecha_creacion: Optional[datetime] = None
    #creado_por: Optional[str] = Field(default=None, max_length=50)
    #fecha_modificacion: Optional[datetime] = None
   # modificado_por: Optional[str] = Field(default=None, max_length=50)
    #estado: Optional[bool] = True

   # administrador: Optional["Administrador"] = Relationship(back_populates="usuario")
