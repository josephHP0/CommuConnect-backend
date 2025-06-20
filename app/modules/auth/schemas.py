from pydantic import BaseModel
from app.core.enums import TipoUsuario

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_rol: TipoUsuario


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