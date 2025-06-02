from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
class Sesion(SQLModel, table=True):
    __tablename__ = "sesion"
    id_sesion: Optional[int] = Field(default=None, primary_key=True)
    id_servicio: Optional[int] = Field(foreign_key="servicio.id_servicio")

    tipo: Optional[str] = Field(default=None, max_length=20)  # ENUM('Virtual', 'Presencial')
    descripcion: str = Field(max_length=100)
    inicio: Optional[datetime] = None
    fin: Optional[datetime] = None

    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[bool] = Field(default=True)

    sesiones_virtuales: List["SesionVirtual"] = Relationship(back_populates="sesion")
    sesiones_presenciales: List["SesionPresencial"] = Relationship( back_populates="sesion",sa_relationship_kwargs={"lazy": "selectin"})

class SesionVirtual(SQLModel, table=True):
    __tablename__ = "sesion_virtual"
    id_sesion_virtual: Optional[int] = Field(default=None, primary_key=True)
    id_sesion: Optional[int] = Field(foreign_key="sesion.id_sesion")
    id_profesional: Optional[int] = Field(foreign_key="profesional.id_profesional")

    doc_asociado: Optional[bytes] = None
    url_meeting: Optional[str] = Field(default=None, max_length=500)
    url_archivo: Optional[str] = Field(default=None, max_length=500)

    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)

    estado: Optional[bool] = Field(default=True)

    # Relaciones (si tienes modelos para Sesion y Profesional)
    sesion: Optional["Sesion"] = Relationship(back_populates="sesiones_virtuales")

class SesionPresencial(SQLModel, table=True):
    __tablename__ = "sesion_presencial"

    id_sesion_presencial: Optional[int] = Field(default=None, primary_key=True)
    id_sesion: Optional[int] = Field(foreign_key="sesion.id_sesion")
    id_local: Optional[int] = Field(foreign_key="local.id_local")
    capacidad: Optional[int] = None

    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[bool] = Field(default=True)

    # Relaciones inversas
    sesion: Optional["Sesion"] = Relationship(back_populates="sesiones_presenciales")
