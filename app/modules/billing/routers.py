from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from app.modules.billing.models import Plan
from app.modules.communities.models import ComunidadXPlan
from .services import crear_inscripcion, crear_pago_pendiente, get_planes, pagar_pendiente
from .schemas import DetalleInscripcionOut, PlanOut, InfoInscripcionOut
from typing import List, Optional
from app.modules.billing.services import tiene_membresia_asociada
from app.modules.billing.schemas import MembresiaAsociadaOut
from app.modules.billing.services import tiene_membresia_activa_en_comunidad
from app.modules.billing.schemas import ValidacionMembresiaOut
from app.modules.billing.services import tiene_topes_disponibles

def nombre(self):
    raise NotImplementedError

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

# Nuevo endpoint para congelar membresía (inscripción)
@router.post("/inscripcion/{id_inscripcion}/congelar")
def congelar_membresia(
    id_inscripcion: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    from .services import congelar_inscripcion
    inscripcion = congelar_inscripcion(session, id_inscripcion, current_user.email)
    return {"ok": True, "message": "Inscripción congelada exitosamente", "inscripcion_id": inscripcion.id_inscripcion}

# Nuevo endpoint para reactivar membresía (inscripción)
@router.post("/inscripcion/{id_inscripcion}/reactivar")
def reactivar_membresia(
    id_inscripcion: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    from .services import reactivar_inscripcion
    inscripcion = reactivar_inscripcion(session, id_inscripcion, current_user.email)
    return {"ok": True, "message": "Inscripción reactivada exitosamente", "inscripcion_id": inscripcion.id_inscripcion}

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


@router.get("/usuario/comunidad/{id_comunidad}/inscripcion-id")
def obtener_id_inscripcion(
    id_comunidad: int,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id),
):
    from sqlmodel import select
    from .services import Inscripcion
    inscripcion = session.exec(
        select(Inscripcion).where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad
        )
    ).first()
    if not inscripcion:
        return {"detail": "No existe inscripción para este usuario en esta comunidad"}
    return {
        "id_inscripcion": inscripcion.id_inscripcion,
        "estado": inscripcion.estado
    }
 
@router.post("/inscripcion/{id_inscripcion}/cancelar")
def cancelar_membresia(
    id_inscripcion: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    from sqlmodel import select
    from .services import Inscripcion
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        return {"detail": "Inscripción no encontrada"}
    inscripcion.estado = 3  # Pendiente de pago
    inscripcion.modificado_por = current_user.email
    from datetime import datetime
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return {"ok": True, "message": "Membresía cancelada, ahora está pendiente de pago", "inscripcion_id": inscripcion.id_inscripcion}

from app.modules.billing.schemas import InfoInscripcionOut

@router.get("/usuario/comunidad/{id_comunidad}/info-inscripcion", response_model=InfoInscripcionOut)
def obtener_info_inscripcion(
    id_comunidad: int,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id),
):
    from sqlmodel import select
    from .services import Inscripcion, DetalleInscripcion
    from app.modules.billing.models import Plan

    inscripcion = session.exec(
        select(Inscripcion).where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad
        )
    ).first()
    if not inscripcion:
        return {"detail": "No existe inscripción para este usuario en esta comunidad"}

    plan = session.get(Plan, inscripcion.id_plan)
    if not plan:
        return {"detail": "No existe plan asociado a la inscripción"}

    detalle = session.exec(
        select(DetalleInscripcion).where(
            DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
        )
    ).first()

    periodo = "Anual" if inscripcion.id_plan and inscripcion.id_plan % 2 == 1 else "Mensual"
    fecha_fin = detalle.fecha_fin.isoformat() if detalle and detalle.fecha_fin else None
    fecha_incio = detalle.fecha_inicio.isoformat() if detalle and detalle.fecha_inicio else None
    topes_disponibles = detalle.topes_disponibles if detalle else None

    return InfoInscripcionOut(
        id_inscripcion=inscripcion.id_inscripcion, # type: ignore
        estado=inscripcion.estado,
        titulo=plan.titulo,
        descripcion_plan=plan.descripcion,
        precio=float(plan.precio),
        periodo=periodo,
        fecha_fin=fecha_fin,
        fecha_inicio=fecha_incio,
        topes_disponibles = "Ilimitado" if detalle and detalle.topes_disponibles and detalle.topes_disponibles > 200 else (detalle.topes_disponibles if detalle else None) # type: ignore
    )