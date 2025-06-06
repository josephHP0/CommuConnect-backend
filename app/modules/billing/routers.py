from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from app.modules.billing.models import Plan
from app.modules.communities.models import ComunidadXPlan
from .services import crear_inscripcion, crear_pago_pendiente, get_planes, pagar_pendiente
from .schemas import DetalleInscripcionOut, PlanOut
from typing import List, Optional

router = APIRouter()

#Lista los 4 planes disponibles
@router.get("/planes", response_model=List[PlanOut])
def listar_planes(session: Session = Depends(get_session)):
    planes = get_planes(session)
    return [PlanOut.from_orm(plan) for plan in planes]

@router.get("/comunidades/{id_comunidad}/planes", response_model=List[PlanOut])
def obtener_planes_por_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session)
):
    planes_ids = session.exec(
        select(ComunidadXPlan.id_plan).where(ComunidadXPlan.id_comunidad == id_comunidad)
    ).all()
    if not planes_ids:
        return []
    planes = session.exec(
        select(Plan).where(Plan.id_plan.in_(planes_ids)) # type: ignore
    ).all()
    return [PlanOut.from_orm(plan) for plan in planes]


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
    # Si se selecciona un plan, crear pago pendiente si no hay id_pago
    if id_plan and not id_pago:
        pago = crear_pago_pendiente(session, id_plan, current_user.email)
        id_pago = pago.id_pago

    return crear_inscripcion(
        session,
        id_plan,
        id_comunidad,
        id_cliente,
        id_pago,
        current_user.email
    )


#Endpoint para la pasarela de pago, necesita la comunidad relacionada al pago
@router.post("/comunidades/{id_comunidad}/pagar")
def pagar_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id),
    current_user=Depends(get_current_user)
):
    pagar_pendiente(
        session,
        id_cliente,
        id_comunidad,
        current_user.email
    )
    return {"ok": True, "message": "Pago realizado exitosamente"}

