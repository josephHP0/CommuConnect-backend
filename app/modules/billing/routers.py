from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from app.modules.billing.models import Plan
from app.modules.communities.models import ComunidadXPlan
from .services import crear_inscripcion, crear_pago_pendiente, get_planes, pagar_pendiente
from .schemas import DetalleInscripcionOut, PlanOut
from typing import List, Optional
from app.modules.billing.services import tiene_membresia_asociada
from app.modules.billing.schemas import MembresiaAsociadaOut
from app.modules.billing.services import tiene_membresia_activa_en_comunidad
from app.modules.billing.schemas import ValidacionMembresiaOut
from app.modules.billing.services import tiene_topes_disponibles
from app.modules.billing.schemas import TieneTopesOut
from app.modules.billing.services import es_plan_con_topes
from app.modules.billing.schemas import EsPlanConTopesOut

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

#Este endpoint es útil para saber rápidamente si un cliente ya está inscrito 
#activamente en alguna comunidad. Ideal para validar antes de mostrar contenido exclusivo,
#planes, reservas, etc.
@router.get("/usuario/validar-membresia-asociada", response_model=MembresiaAsociadaOut)
def validar_membresia_asociada(
    session: Session        = Depends(get_session),
    cliente_id: int         = Depends(get_current_cliente_id),
):
    ok = tiene_membresia_asociada(session, cliente_id)
    return MembresiaAsociadaOut(tieneMembresiaAsociada=ok)


"""Este endpoint GET /usuario/validar-membresia/{id_comunidad} verifica si el 
cliente autenticado tiene una membresía activa en una comunidad específica. 
Utiliza su id_cliente (extraído del token JWT) y el id_comunidad del path. 
Consulta la base de datos y devuelve un JSON con el resultado:
json: { "tieneMembresiaActiva": true | false }
Solo retorna true si existe una inscripción activa (estado = 1) para ese cliente en esa comunidad.
"""

@router.get("/usuario/validar-membresia/{id_comunidad}", response_model=ValidacionMembresiaOut)
def validar_membresia_por_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    cliente_id: int = Depends(get_current_cliente_id),
):
    tiene_membresia = tiene_membresia_activa_en_comunidad(session, cliente_id, id_comunidad)
    return ValidacionMembresiaOut(tieneMembresiaActiva=tiene_membresia)


@router.get("/usuario/comunidad/{id_comunidad}/tiene-topes", response_model=TieneTopesOut)
def validar_tiene_topes(
    id_comunidad: int,
    session: Session = Depends(get_session),
    cliente_id: int = Depends(get_current_cliente_id),
):
    tiene = tiene_topes_disponibles(session, cliente_id, id_comunidad)
    return TieneTopesOut(tieneTopes=tiene)


@router.get("/usuario/plan/{id_inscripcion}/es-con-topes", response_model=EsPlanConTopesOut)
def validar_si_plan_es_con_topes(
    id_inscripcion: int,
    session: Session = Depends(get_session)
):
    resultado = es_plan_con_topes(session, id_inscripcion)
    return EsPlanConTopesOut(esPlanConTopes=resultado)