from typing import Optional, Literal
from datetime import date
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import SQLModel

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

class UsuarioRead(SQLModel):
    """
    Esquema de salida para mostrar usuarios (sin contraseña).
    No se crea como tabla: no lleva `table=True`.
    """
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    estado: Optional[bool]

    class Config:
        orm_mode = True
        from_attributes = True  # útil para compatibilidad extra