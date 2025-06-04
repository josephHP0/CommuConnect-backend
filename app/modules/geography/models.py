from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class Departamento(SQLModel, table=True):
    id_departamento: int = Field(primary_key=True)
    nombre: str = Field(max_length=45)

    # Relación uno a muchos con distrito
    distritos: List["Distrito"] = Relationship(back_populates="departamento")


class Distrito(SQLModel, table=True):
    id_distrito: int = Field(primary_key=True)
    id_departamento: int = Field(foreign_key="departamento.id_departamento")
    nombre: str = Field(max_length=45)
    imagen: Optional[bytes] = None

    # Relación inversa: muchos a uno (sin Optional aquí)
    departamento: Departamento = Relationship(back_populates="distritos")
