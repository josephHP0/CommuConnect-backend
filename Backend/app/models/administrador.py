from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from app.models.usuario import Usuario

class Administrador(SQLModel, table=True):
    id_administrador: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")

    usuario: Optional[Usuario] = Relationship(back_populates="administrador")
