from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal, Optional
from datetime import date, datetime

from app.core.enums import TipoDocumento

'''
class UserCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    repetir_password: str
    tipo_documento: Literal['DNI', 'CARNET DE EXTRANJERÍA']
    num_doc: str
    numero_telefono: str
    id_departamento: int
    id_distrito: int
    direccion: str
    fecha_nac: date
    genero: str
    talla: int = Field(..., gt=0)
    peso: int = Field(..., gt=0)
'''
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
