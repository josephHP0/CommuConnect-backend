from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class ServicioResumen(BaseModel):
    nombre: str

    class Config:
        orm_mode = True

class ProfesionalRead(BaseModel):
    id_profesional: int
    nombre_completo: Optional[str]
    id_servicio: Optional[int]
    formulario: Optional[str]
    fecha_creacion: Optional[datetime]
    creado_por: Optional[str]
    fecha_modificacion: Optional[datetime]
    modificado_por: Optional[str]
    estado: Optional[bool]

    model_config = ConfigDict(from_attributes=True)