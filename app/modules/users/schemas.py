from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from datetime import date

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
