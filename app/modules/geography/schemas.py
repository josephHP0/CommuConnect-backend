from pydantic import BaseModel
from typing import Optional

class UsuarioActualizar(BaseModel):
    numero_telefono: Optional[str]
    id_departamento: Optional[int]
    id_distrito: Optional[int]
    direccion: Optional[str]
    genero: Optional[str]
    talla: Optional[float]
    peso: Optional[float]
