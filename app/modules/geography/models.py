from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

class Distrito(SQLModel, table=True):
    id_distrito: int = Field(primary_key=True)
    id_departamento: int = Field(foreign_key="departamento.id_departamento")
    nombre: str = Field(max_length=45)
    imagen: Optional[bytes] = None

    departamento: Optional["Departamento"] = Relationship(back_populates="distritos")

class Departamento(SQLModel, table=True):
    id_departamento: int = Field(primary_key=True)
    nombre: str = Field(max_length=45)

    distritos: List["Distrito"] = Relationship(back_populates="departamento")