from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, date

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=60)
    apellido: str = Field(max_length=60)
    email: str = Field(max_length=60, unique=True)
    password: str = Field(max_length=60)
    tipo: Optional[str] = Field(default="CLIENTE", max_length=20)
    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[bool] = Field(default=True)

    cliente: Optional["Cliente"] = Relationship(back_populates="usuario")
    administrador: Optional["Administrador"] = Relationship(back_populates="usuario")

class Administrador(SQLModel, table=True):
    id_administrador: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")

    usuario: Optional[Usuario] = Relationship(back_populates="administrador")

class Cliente(SQLModel, table=True):
    id_cliente: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")

    tipo_documento: str = Field(max_length=20)
    num_doc: str = Field(max_length=45, unique=True)
    numero_telefono: str = Field(max_length=45)
    id_departamento: int
    id_distrito: int
    direccion: Optional[str] = Field(default=None, max_length=350)
    fecha_nac: Optional[date] = None
    genero: Optional[str] = Field(default=None, max_length=45)
    talla: int
    peso: int

    usuario: Optional[Usuario] = Relationship(back_populates="cliente")
