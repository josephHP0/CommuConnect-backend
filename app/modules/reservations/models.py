from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Profesional(SQLModel, table=True):
    __tablename__ = "profesional"
    id_profesional: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int
    formulario: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    creado_por: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = None
    estado: Optional[bool] = True

    sesiones_virtuales: List["SesionVirtual"] = Relationship(back_populates="profesional")



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
    profesional: Optional["Profesional"] = Relationship(back_populates="sesiones_virtuales")