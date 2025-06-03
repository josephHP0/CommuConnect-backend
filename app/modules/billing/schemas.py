from pydantic import BaseModel
from typing import Optional

class PlanOut(BaseModel):
    id_plan: int
    titulo: str
    descripcion: str
    topes: int
    precio: float


class UsoTopesOut(BaseModel):
    plan: Optional[str] = None
    topes_disponibles: Optional[int] = None
    topes_consumidos: Optional[int] = None
    estado: str