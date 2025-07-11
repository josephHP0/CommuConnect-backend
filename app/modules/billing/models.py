from __future__ import annotations
from sqlalchemy import Enum as SAEnum, DECIMAL, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import DECIMAL, Column
from sqlalchemy import Integer
from app.core.enums import MetodoPago

class Plan(SQLModel, table=True):
    id_plan: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=100)
    descripcion: str = Field(max_length=300)
    duracion: Optional[int] = None  # <-- Hazlo opcional
    topes: Optional[int] = None     # <-- También puede ser opcional
    precio: float = Field(sa_column=Column(DECIMAL(10, 2)))
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: int = 1

class Pago(SQLModel, table=True):
    id_pago: Optional[int] = Field(default=None, primary_key=True)
    monto: float = Field(sa_column=Column(DECIMAL(10, 2)))
    fecha_pago: Optional[datetime] = None
    metodo_pago: Optional[MetodoPago] = Field(default=None, sa_column=Column(SAEnum(MetodoPago)))
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: int = 0  # 0 = pendiente, 1 = pagado

class Inscripcion(SQLModel, table=True):
    id_inscripcion: Optional[int] = Field(default=None, primary_key=True)
    id_plan: Optional[int] = Field(default=None, foreign_key="plan.id_plan")
    id_comunidad: int = Field(foreign_key="comunidad.id_comunidad")
    id_cliente: int = Field(foreign_key="cliente.id_cliente")
    id_pago: Optional[int] = Field(default=None, foreign_key="pago.id_pago")
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: int = 1  # o el valor que corresponda por defecto

class DetalleInscripcion(SQLModel, table=True):
    __tablename__ = "detalle_inscripcion" # type: ignore

    id_registros_inscripcion: Optional[int] = Field(default=None, primary_key=True)
    id_inscripcion: int = Field(foreign_key="inscripcion.id_inscripcion")
    fecha_registro: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    topes_disponibles: int
    topes_consumidos: int
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: str = Field(max_length=50)
    fecha_modificacion: Optional[datetime] = None
    modificado_por: Optional[str] = Field(default=None, max_length=50)
    estado: int

class Suspension(SQLModel, table=True):
        __tablename__ = "suspension" # type: ignore
        id_suspension: int = Field(default=None, primary_key=True)
        id_cliente: int
        id_inscripcion: int
        motivo: str
        fecha_inicio: datetime
        fecha_fin: datetime
        archivo: Optional[bytes] = None # type: ignore
        fecha_creacion: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"nullable": False})
        creado_por: str
        fecha_modificacion: Optional[datetime] = None
        modificado_por: Optional[str] = Field(default=None, max_length=50)
        estado: int