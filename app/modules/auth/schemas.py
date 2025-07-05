from pydantic import BaseModel
from app.core.enums import TipoUsuario
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_rol: TipoUsuario
    id_cliente: Optional[int] = None


class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    email: str
    password: str
    creado_por: str
    tipo: TipoUsuario

class CambioPasswordIn(BaseModel):
    actual: str
    nueva: str
    repetir: str 