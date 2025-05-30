from pydantic import BaseModel

class PlanOut(BaseModel):
    id_plan: int
    titulo: str
    descripcion: str
    topes: int
    precio: float