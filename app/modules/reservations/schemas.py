from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProfesionalRead(BaseModel):
    id_profesional: int
    id_usuario: int
    formulario: Optional[str]
    fecha_creacion: Optional[datetime]
    creado_por: Optional[str]
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: Optional[bool]

    class Config:
        orm_mode = True

