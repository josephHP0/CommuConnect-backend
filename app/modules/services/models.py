from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, ClassVar, TYPE_CHECKING, List
from datetime import datetime
from app.core.enums import ModalidadServicio

class ComunidadXServicio(SQLModel, table=True):
    __tablename__: ClassVar[str] = "comunidadxservicio" # type: ignore[assignment]
    id_comunidad: int = Field(foreign_key="comunidad.id_comunidad", primary_key=True)
    id_servicio: int = Field(foreign_key="servicio.id_servicio", primary_key=True)
    estado: int = Field(default=1)  # 1=Activo, 0=Inactivo

class Servicio(SQLModel, table=True):
    id_servicio: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=100)
    imagen: Optional[bytes] = None
    modalidad: ModalidadServicio  # Enum: 'Virtual' o 'Presencial'
    fecha_creacion: datetime
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: int  # tinyint en MySQL, usualmente 0/1
    locales: List["Local"] = Relationship(back_populates="servicio")
    profesionales: List["Profesional"] = Relationship(back_populates="servicio")

class Local(SQLModel, table=True):
    __tablename__ = "local" # type: ignore
    id_local: Optional[int] = Field(default=None, primary_key=True)
    id_departamento: int = Field(foreign_key="departamento.id_departamento")
    id_distrito: int = Field(foreign_key="distrito.id_distrito")
    id_servicio: Optional[int] = Field(default=None, foreign_key="servicio.id_servicio")

    direccion_detallada: Optional[str] = Field(default=None, max_length=350)
    responsable: Optional[str] = Field(default=None, max_length=45)
    nombre: Optional[str] = Field(default=None, max_length=100)
    link: Optional[str] = Field(default=None, max_length=200)

    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[int] = Field(default=1)

    servicio: Optional["Servicio"] = Relationship(back_populates="locales")

class Profesional(SQLModel, table=True):
    __tablename__ = "profesional" # type: ignore

    id_profesional: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=100)
    id_servicio: Optional[int] = Field(default=None, foreign_key="servicio.id_servicio")
    formulario: Optional[str] = Field(default=None, max_length=200)

    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[int] = Field(default=1)

    # Relación inversa con Servicio
    servicio: Optional["Servicio"] = Relationship(back_populates="profesionales")

