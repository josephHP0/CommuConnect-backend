from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from typing import Literal, Optional
from datetime import date, datetime
from utils.datetime_utils import convert_utc_to_local
from pydantic import BaseModel, EmailStr

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

    @validator('fecha_creacion', pre=True, always=True)
    def localize_dates(cls, v):
        if v:
            return convert_utc_to_local(v)
        return v

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
    email: Optional[str]  # <-- Añadido para permitir cambio de contraseña
    password: Optional[str]
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

    @validator('fecha_creacion', 'fecha_modificacion', pre=True, always=True)
    def localize_dates(cls, v):
        if v:
            return convert_utc_to_local(v)
        return v

    class Config:
        from_attributes = True

class ClienteUsuarioFull(BaseModel):
    id_cliente: int
    tipo_documento: str
    num_doc: str
    numero_telefono: str
    id_departamento: int
    departamento_nombre: Optional[str] = None
    id_distrito: int
    distrito_nombre: Optional[str] = None
    direccion: Optional[str]
    fecha_nac: Optional[date]
    genero: Optional[str]
    talla: float
    peso: float
    usuario: UsuarioBase

    class Config:
        from_attributes = True

class ClienteUpdateIn(BaseModel):
    numero_telefono: Optional[str] = None
    departamento_nombre: Optional[str] = None
    distrito_nombre: Optional[str] = None
    direccion: Optional[str] = None
    genero: Optional[str] = None
    talla: Optional[float] = None
    peso: Optional[float] = None


class SolicitarRecuperacionSchema(BaseModel):
    email: EmailStr

class CambioContrasenaSchema(BaseModel):
    token: str = Field(..., description="Token JWT recibido por correo")
    nueva_contrasena: str = Field(..., min_length=8, description="Nueva contraseña")

class VerificarTokenSchema(BaseModel):
    token: str

