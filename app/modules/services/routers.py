from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.db import get_session
from app.modules.services.services import obtener_profesionales_por_servicio
from typing import List
from app.modules.services.schemas import ProfesionalRead

router = APIRouter()

@router.get("/profesionales/{id_servicio}", response_model=List[ProfesionalRead])
def listar_profesionales_por_servicio(id_servicio: int, session: Session = Depends(get_session)):
    try:
        resultado = obtener_profesionales_por_servicio(session, id_servicio)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")