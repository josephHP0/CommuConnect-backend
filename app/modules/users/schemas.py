from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal, Optional
from datetime import date, datetime

from app.core.enums import TipoDocumento, TipoUsuario

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    tipo: Optional[str] = "CLIENTE"
    class Config:
        from_attributes = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioRead(UsuarioBase):
    id_usuario: int
    estado: bool
    fecha_creacion: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ClienteBase(BaseModel):
    tipo_documento: TipoDocumento
    num_doc: str
    numero_telefono: str
    id_departamento: int
    id_distrito: int
    direccion: Optional[str] = None
    fecha_nac: Optional[date] = None
    genero: Optional[str] = None
    talla: int
    peso: int

class ClienteCreate(ClienteBase):
    nombre: str
    apellido: str
    email: str
    password: str
    
class ClienteRead(ClienteBase):
    id_cliente: int
    id_usuario: int

    model_config = ConfigDict(from_attributes=True)

class AdministradorCreate(BaseModel):
    nombre: str
    apellido: str
    email: str
    password: str

class AdministradorRead(BaseModel):
    id_administrador: int
    id_usuario: int

    model_config = ConfigDict(from_attributes=True)

class ClienteUpdate(BaseModel):
    nombre: Optional[str]
    apellido: Optional[str]
    email: Optional[str]
    password: Optional[str]  # <-- Añadido para permitir cambio de contraseña
    tipo_documento: Optional[str]
    num_doc: Optional[str]
    numero_telefono: Optional[str]
    id_departamento: Optional[int]
    id_distrito: Optional[int]
    direccion: Optional[str]
    fecha_nac: Optional[date]
    genero: Optional[str]
    talla: Optional[float]
    peso: Optional[float]

    model_config = ConfigDict(from_attributes=True)

class ClienteInfo(BaseModel):
    id_cliente: int
    tipo_documento: TipoDocumento
    num_doc: str
    numero_telefono: str
    id_departamento: int
    id_distrito: int
    direccion: Optional[str]
    fecha_nac: Optional[date]
    genero: Optional[str]
    talla: int
    peso: int

    class Config:
        from_attributes = True

class UsuarioClienteFull(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    tipo: TipoUsuario
    fecha_creacion: Optional[datetime]
    creado_por: Optional[str]
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: bool
    cliente: Optional[ClienteInfo]

    class Config:
        from_attributes = True

class ClienteUsuarioFull(BaseModel):
    id_cliente: int
    tipo_documento: str
    num_doc: str
    numero_telefono: str
    id_departamento: int
    id_distrito: int
    direccion: Optional[str]
    fecha_nac: Optional[date]
    genero: Optional[str]
    talla: float
    peso: float
    usuario: UsuarioBase

    class Config:
        from_attributes = True

class ClienteUpdateIn(BaseModel):
    numero_telefono: Optional[str]
    id_departamento: Optional[int]
    id_distrito: Optional[int]
    direccion: Optional[str]
    genero: Optional[str]
    talla: Optional[int]
    peso: Optional[int]