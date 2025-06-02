from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session
from app.core.db import get_session
from app.modules.reservations.services import obtener_fechas_presenciales
from app.modules.reservations.schemas import FechasPresencialesResponse, HorasPresencialesResponse

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.get(
    "/fechas-presenciales",
    response_model=FechasPresencialesResponse,
    summary="Fechas de sesiones presenciales sin repetirse",
)
def listar_fechas_presenciales(
    *,
    id_servicio: int = Query(..., description="ID del servicio a filtrar"),
    id_distrito: int = Query(..., description="ID del distrito a filtrar"),
    id_local: int = Query(..., description="ID del local a filtrar"),
    session: Session = Depends(get_session),
):
    # Llamamos al service para hacer la consulta y validación
    fechas = obtener_fechas_presenciales(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local
    )

    # Si quisiéramos distinguir “local no existe o no pertenece” de “no hay sesiones”,
    # el service podría lanzar excepción en ese caso y aquí atraparla:
    if fechas is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El local no existe o no pertenece al distrito indicado"
        )

    return FechasPresencialesResponse(fechas=fechas)

@router.get(
    "/horas-presenciales",
    response_model=HorasPresencialesResponse,
    summary="Horas de sesiones presenciales para un servicio/local/fecha dado",
)
def listar_horas_presenciales(
    *,
    id_servicio: int = Query(..., description="ID del servicio a filtrar"),
    id_distrito: int = Query(..., description="ID del distrito a filtrar"),
    id_local: int = Query(..., description="ID del local a filtrar"),
    fecha: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    session: Session = Depends(get_session),
):
    """
    Retorna todas las horas (sin repetir) en que hay sesiones presenciales
    para el servicio `id_servicio`, en el distrito `id_distrito`, 
    local `id_local` y la fecha `fecha` (solo día/mes/año).
    """

    horas = obtener_horas_presenciales(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local,
        fecha_seleccionada=fecha
    )

    # Si el service devolvió lista vacía y queremos distinguir “local inválido” 
    # de “no hay sesiones a esa hora”, podríamos hacer:
    if horas == []:
        # Aquí asumimos que `[]` puede significar “local inválido” o “sin horas disponibles”.
        # Si quisieras un 404 distinto a “no hay sesiones”:
        #    raise HTTPException(404, "Local no existe o no pertenece al distrito")
        # Pero si simplemente quieres “¿no hay horas disponibles?”, devuelves [] sin error.
        pass

    return HorasPresencialesResponse(horas=horas)