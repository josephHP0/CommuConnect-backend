from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from typing import ClassVar


class ComunidadXServicio(SQLModel, table=True):
    __tablename__: ClassVar[str] = "comunidadxservicio" # type: ignore[assignment]
    id_comunidad: int = Field(foreign_key="comunidad.id_comunidad", primary_key=True)
    id_servicio: int = Field(foreign_key="servicio.id_servicio", primary_key=True)

class Servicio(SQLModel, table=True):
    id_servicio: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    descripccion: Optional[str] = Field(default=None, max_length=100)
    imagen: Optional[bytes] = None
    modalidad: str = Field(max_length=10)  # Enum: 'Virtual' o 'Presencial'
    fecha_creacion: datetime
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: int  # tinyint en MySQL, usualmente 0/1
