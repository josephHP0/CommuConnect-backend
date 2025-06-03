from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from .services import crear_inscripcion, crear_pago_pendiente, get_planes, pagar_pendiente
from .schemas import PlanOut
from typing import List, Optional

router = APIRouter()

#Lista los 4 planes disponibles
@router.get("/planes", response_model=List[PlanOut])
def listar_planes(session: Session = Depends(get_session)):
    return get_planes(session)

#Endpoint para la pantalla "Elige tu plan", genera una orden de pago
@router.post("/planes/{id_plan}/seleccionar")
def seleccionar_plan(
    id_plan: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    return crear_pago_pendiente(session, id_plan, current_user.email)


#Endpoint para registrar una inscripcion, necesita el id de la comunidad y opcionalmente el id del plan y del pago
#Se da a la vez de seleccionar plan ya sea con un plan elegido o con el boton de omitir
@router.post("/inscripcion")
def registrar_inscripcion(
    id_comunidad: int,
    id_plan: Optional[int] = None,
    id_pago: Optional[int] = None,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id),
    current_user=Depends(get_current_user)
):
    return crear_inscripcion(
        session,
        id_plan,
        id_comunidad,
        id_cliente,
        id_pago,
        current_user.email
    )


#Endpoint para la pasaerla de pago, necesita la comunidad relacionada al pago
@router.post("/comunidades/{id_comunidad}/pagar")
def pagar_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id),
    current_user=Depends(get_current_user)
):
    return pagar_pendiente(
        session,
        id_cliente,
        id_comunidad,
        current_user.email
    )


