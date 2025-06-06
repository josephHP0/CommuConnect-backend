from __future__ import annotations
from typing import Optional, ClassVar, TYPE_CHECKING, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Comunidad(SQLModel, table=True):
    id_comunidad: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    slogan: Optional[str] = Field(default=None, max_length=350)
    imagen: Optional[bytes] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = Field(default=None)
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: bool = Field(default=True)

class ClienteXComunidad(SQLModel, table=True):
    id_cliente: int = Field(foreign_key="cliente.id_cliente", primary_key=True)
    id_comunidad: int = Field(foreign_key="comunidad.id_comunidad", primary_key=True)

class ComunidadXPlan(SQLModel, table=True):
    __tablename__: ClassVar[str] = "comunidadxplan" # type: ignore

    id_comunidad: int = Field(foreign_key="comunidad.id_comunidad",primary_key=True)
    id_plan: int = Field(foreign_key="plan.id_plan",primary_key=True)

    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = Field(default=None, max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[int] = Field(default=1)