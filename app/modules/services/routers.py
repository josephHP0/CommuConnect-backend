from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.services.services import obtener_profesionales_por_servicio
from typing import List
from app.modules.services.schemas import ProfesionalRead
from app.modules.services.services import obtener_distritos_por_servicio_service
from app.modules.services.schemas import DistritoOut
from app.modules.services.models import Local
from app.modules.services.schemas import LocalOut
router = APIRouter()

@router.get("/profesionales/{id_servicio}", response_model=List[ProfesionalRead])
def listar_profesionales_por_servicio(id_servicio: int, session: Session = Depends(get_session)):
    try:
        resultado = obtener_profesionales_por_servicio(session, id_servicio)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    
@router.get("/usuario/servicio/{id_servicio}/distritos", response_model=List[DistritoOut])
def obtener_distritos_por_servicio(
    id_servicio: int,
    session: Session = Depends(get_session)
):
    return obtener_distritos_por_servicio_service(session, id_servicio)


@router.get("/servicio/{id_servicio}/distrito/{id_distrito}/locales", response_model=List[LocalOut])
def obtener_locales_por_servicio_y_distrito(
    id_servicio: int,
    id_distrito: int,
    session: Session = Depends(get_session)
):
    query = select(Local).where(
        Local.id_servicio == id_servicio,
        Local.id_distrito == id_distrito,
        Local.estado == 1
    )

    locales = session.exec(query).all()

    if not locales:
        raise HTTPException(status_code=404, detail="No se encontraron locales activos para ese servicio y distrito.")

    return locales