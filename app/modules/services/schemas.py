from pydantic import BaseModel

class ServicioResumen(BaseModel):
    nombre: str

    class Config:
        orm_mode = True