from datetime import date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from app.modules.billing.models import DetalleInscripcion, Inscripcion, Pago, Plan, Suspension
from app.modules.communities.models import Comunidad, ComunidadXPlan
from app.modules.users.models import Cliente, Usuario
from utils.email_brevo import send_membership_activated_email, send_membership_cancelled_email, send_suspension_accepted_email
from .services import actualizar_plan, agregar_plan_a_comunidad_serv, crear_inscripcion, crear_pago_pendiente, crear_plan, eliminar_plan_logico, get_planes, obtener_planes_no_asociados, obtener_planes_por_comunidad, pagar_pendiente
from .schemas import ComunidadXPlanCreate, DetalleInscripcionOut, DetalleInscripcionPagoOut, InscripcionResumenOut, PlanOut, InfoInscripcionOut, SuspensionEstadoOut, PlanCreate, PlanUpdate
from typing import List, Optional
from app.modules.billing.services import tiene_membresia_asociada
from app.modules.billing.schemas import MembresiaAsociadaOut
from app.modules.billing.services import tiene_membresia_activa_en_comunidad
from app.modules.billing.schemas import ValidacionMembresiaOut
from app.modules.billing.services import tiene_topes_disponibles
from datetime import datetime
from sqlalchemy import desc

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

@router.get("/por-comunidad/{id_comunidad}", response_model=list[PlanOut])
def listar_planes_por_comunidad(id_comunidad: int, db: Session = Depends(get_session)):
    return obtener_planes_por_comunidad(db, id_comunidad)


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

    cliente = session.get(Cliente, id_cliente)
    usuario = session.get(Usuario, cliente.id_usuario) if cliente else None

    inscripcion = session.exec(
        select(Inscripcion)
        .where(Inscripcion.id_cliente == id_cliente)
        .where(Inscripcion.id_comunidad == id_comunidad)
    ).first()

    plan = session.get(Plan, inscripcion.id_plan) if inscripcion else None
    comunidad = session.get(Comunidad, id_comunidad)
    detalle = session.exec(
        select(DetalleInscripcion).where(
            DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
        )
    ).first() if inscripcion else None

    if usuario and plan and comunidad and detalle:
        details = {
            "nombre_usuario": usuario.nombre if hasattr(usuario, "nombre") else usuario.email,
            "nombre_plan": plan.titulo,
            "nombre_comunidad": comunidad.nombre,
            "fecha_inicio": detalle.fecha_inicio.strftime("%Y-%m-%d") if detalle.fecha_inicio else "",
            "fecha_fin": detalle.fecha_fin.strftime("%Y-%m-%d") if detalle.fecha_fin else "",
            "precio": float(plan.precio),
        }
        try:
            send_membership_activated_email(usuario.email, details)
            print("Correo de membresía activa enviado a:", usuario.email)
        except Exception as e:
            print("Error enviando correo de membresía activa:", e)

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

@router.post("/inscripcion/{id_inscripcion}/reactivar")
def reactivar_membresia(
    id_inscripcion: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    from .services import reactivar_inscripcion
    inscripcion = reactivar_inscripcion(session, id_inscripcion, current_user.email)

    # Cambia el estado de la suspensión asociada (si existe) a 3 (completada)
    suspension = session.exec(
        select(Suspension)
        .where(Suspension.id_inscripcion == id_inscripcion)
        .where(Suspension.estado.in_([1, 2])) # type: ignore
        .order_by(desc(Suspension.fecha_creacion)) # type: ignore
    ).first()
    if suspension:
        suspension.estado = 3  # Completada
        suspension.modificado_por = current_user.email
        suspension.fecha_modificacion = datetime.utcnow()
        session.add(suspension)
        session.commit()
        session.refresh(suspension)

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

    # Obtener datos para el correo
    cliente = session.get(Cliente, inscripcion.id_cliente)
    usuario = session.get(Usuario, cliente.id_usuario) if cliente else None
    plan = session.get(Plan, inscripcion.id_plan)
    comunidad = session.get(Comunidad, inscripcion.id_comunidad)
    detalle = session.exec(
        select(DetalleInscripcion).where(
            DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
        )
    ).first()

    if usuario and plan and comunidad and detalle:
        details = {
            "nombre_usuario": usuario.nombre if hasattr(usuario, "nombre") else usuario.email,
            "nombre_plan": plan.titulo,
            "nombre_comunidad": comunidad.nombre,
            "fecha_inicio": detalle.fecha_inicio.strftime("%Y-%m-%d") if detalle.fecha_inicio else "",
            "fecha_cancelacion": inscripcion.fecha_modificacion.strftime("%Y-%m-%d") if inscripcion.fecha_modificacion else "",
        }
        try:
            send_membership_cancelled_email(usuario.email, details)
            print("Correo de cancelación de membresía enviado a:", usuario.email)
        except Exception as e:
            print("Error enviando correo de cancelación de membresía:", e)


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

    periodo = "Anual" if plan.duracion == 12 else "Mensual"
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
        topes_disponibles = (
            "ilimitado"
            if (plan.topes is None or (detalle and detalle.topes_disponibles is None))
            else (detalle.topes_disponibles if detalle else None)
        )
    )


@router.post("/agregar-plan")
def agregar_plan_a_comunidad(
    data: ComunidadXPlanCreate,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    return agregar_plan_a_comunidad_serv(
        db=db,
        data=data,
        creado_por=current_user.email  # O current_user.nombre_usuario según tu modelo
    )

@router.get("/no-asociados/{id_comunidad}", response_model=list[PlanOut])
def listar_planes_no_asociados(id_comunidad: int, db: Session = Depends(get_session)):
    return obtener_planes_no_asociados(db, id_comunidad)

@router.get("/usuario/inscripciones", response_model=List[InscripcionResumenOut])
def historial_membresias(
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id),
):
    from sqlmodel import select
    from .services import Inscripcion, DetalleInscripcion
    from app.modules.billing.models import Plan

    inscripciones = session.exec(
        select(Inscripcion).where(Inscripcion.id_cliente == id_cliente)
    ).all()

    resultado = []
    for inscripcion in inscripciones:
        plan = session.get(Plan, inscripcion.id_plan)
        detalle = session.exec(
            select(DetalleInscripcion).where(
                DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
            )
        ).first()
        fecha_inicio = None
        if detalle and detalle.fecha_inicio:
            fecha_inicio = detalle.fecha_inicio.astimezone(ZoneInfo("America/Lima")).isoformat()
        resultado.append(
            InscripcionResumenOut(
                id_inscripcion=inscripcion.id_inscripcion, # type: ignore
                fecha_inicio=fecha_inicio,
                titulo_plan=plan.titulo if plan else "",
                precio=float(plan.precio) if plan else 0.0,
            )
        )
    return resultado


@router.get("/inscripcion/{id_inscripcion}/detalle", response_model=DetalleInscripcionPagoOut)
def ver_detalle_pago(
    id_inscripcion: int,
    session: Session = Depends(get_session)
):
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")

    plan = session.get(Plan, inscripcion.id_plan)
    pago = session.get(Pago, inscripcion.id_pago) if inscripcion.id_pago else None

    fecha_pago = None
    hora_pago = None
    if pago and pago.fecha_pago:
        fecha_pago_peru = pago.fecha_pago.astimezone(ZoneInfo("America/Lima"))
        fecha_pago = fecha_pago_peru.date().isoformat()
        hora_pago = fecha_pago_peru.time().isoformat(timespec="seconds")

    return DetalleInscripcionPagoOut(
        nombre_membresia=plan.titulo if plan else "",
        fecha_pago=fecha_pago,
        hora_pago=hora_pago,
        id_pago=pago.id_pago if pago else None,
        tarjeta="**** 1234"
    )

# Endpoint de solicitud de congelamiento de membresía
@router.post("/inscripcion/{id_inscripcion}/solicitar-congelamiento")
def solicitar_congelamiento_membresia(
    id_inscripcion: int,
    fecha_inicio: date,
    fecha_fin: date,
    motivo: str,
    archivo: Optional[bytes] = None,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    current_cliente_id: int = Depends(get_current_cliente_id),
):
    suspension = Suspension(
        id_cliente=current_cliente_id,
        id_inscripcion=id_inscripcion,
        motivo=motivo or "",
        fecha_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
        fecha_fin=datetime.combine(fecha_fin, datetime.min.time()),
        archivo= archivo,
        fecha_creacion=datetime.utcnow(),
        creado_por=current_user.email,
        fecha_modificacion=None,
        modificado_por=None,
        estado=2  # Pendiente
    )
    session.add(suspension)
    session.commit()
    session.refresh(suspension)
    return {"ok": True, "message": "Solicitud de congelamiento registrada y pendiente de aprobación", "id_suspension": suspension.id_suspension}


# Endpoint para aceptar una suspensión de membresía desde el administrador
@router.post("/suspension/{id_suspension}/aceptar")
def aceptar_suspension(
    id_suspension: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    # Busca la suspensión
    suspension = session.get(Suspension, id_suspension)
    if not suspension:
        raise HTTPException(status_code=404, detail="Suspensión no encontrada")

    # Cambia el estado de la suspensión a 1 (aceptada)
    suspension.estado = 1
    suspension.modificado_por = current_user.email
    suspension.fecha_modificacion = datetime.utcnow()
    session.add(suspension)

    # Cambia el estado de la inscripción a 0 (congelado)
    inscripcion = session.get(Inscripcion, suspension.id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    inscripcion.estado = 0
    inscripcion.modificado_por = current_user.email
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)

    session.commit()

    # ... después de session.commit()
    print("Antes de buscar usuario")
    cliente = session.get(Cliente, inscripcion.id_cliente)
    usuario = session.get(Usuario, cliente.id_usuario) if cliente else None
    print("Después de buscar usuario:", usuario)
    if usuario:
        details = {
            "nombre_usuario": usuario.nombre if hasattr(usuario, "nombre") else usuario.email,
            "motivo": suspension.motivo,
            "fecha_inicio": suspension.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": suspension.fecha_fin.strftime("%Y-%m-%d"),
        }
        print("Intentando enviar correo a:", usuario.email)
        try:
            send_suspension_accepted_email(usuario.email, details)
            print("Correo enviado exitosamente a:", usuario.email)
        except Exception as e:
            print("Error enviando correo:", e)

    return {"ok": True, "message": "Suspensión aceptada y membresía congelada exitosamente", "id_suspension": suspension.id_suspension}

# Endpoint para rechazar una suspensión de membresía desde el administrador
@router.post("/suspension/{id_suspension}/rechazar")
def rechazar_suspension(
    id_suspension: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    # Busca la suspensión
    suspension = session.get(Suspension, id_suspension)
    if not suspension:
        raise HTTPException(status_code=404, detail="Suspensión no encontrada")

    # Cambia el estado de la suspensión a 0 (rechazada)
    suspension.estado = 0
    suspension.modificado_por = current_user.email
    suspension.fecha_modificacion = datetime.utcnow()
    session.add(suspension)

    # La inscripción sigue activa (estado 1), no se modifica

    session.commit()
    return {"ok": True, "message": "Suspensión rechazada exitosamente", "id_suspension": suspension.id_suspension}

# Endpoint para listar todas las suspensiones de membresía pendientes
@router.get("/suspensiones/pendientes", response_model=List[Suspension])
def listar_suspensiones_pendientes(
    session: Session = Depends(get_session)
):
    suspensiones = session.exec(
        select(Suspension).where(Suspension.estado == 2)
    ).all()
    return suspensiones

@router.get("/suspensiones/todas", response_model=List[SuspensionEstadoOut])
def listar_todas_suspensiones(
    session: Session = Depends(get_session)
):
    suspensiones = session.exec(select(Suspension)).all()
    estado_map = {0: "Rechazada", 1: "Aceptada", 2: "Pendiente", 3:"Completada"}
    resultado = []
    for s in suspensiones:
        resultado.append(SuspensionEstadoOut(
            id_suspension=s.id_suspension,
            id_cliente=s.id_cliente,
            id_inscripcion=s.id_inscripcion,
            motivo=s.motivo,
            fecha_inicio=s.fecha_inicio.isoformat() if s.fecha_inicio else "",
            fecha_fin=s.fecha_fin.isoformat() if s.fecha_fin else "",
            estado=estado_map.get(s.estado, "Desconocido")
        ))
    return resultado


@router.post("/planes", response_model=PlanOut)
def crear_nuevo_plan(
    plan: PlanCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    nuevo_plan = crear_plan(session, plan, current_user.email)
    return PlanOut.from_orm(nuevo_plan)

@router.delete("/planes/{id_plan}", response_model=PlanOut)
def eliminar_plan(
    id_plan: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    plan = eliminar_plan_logico(session, id_plan, current_user.email)
    return PlanOut.from_orm(plan)

@router.put("/planes/{id_plan}", response_model=PlanOut)
def actualizar_plan_endpoint(
    id_plan: int,
    plan: PlanUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    plan_actualizado = actualizar_plan(session, id_plan, plan, current_user.email)
    return PlanOut.from_orm(plan_actualizado)

@router.get("/planes/{id_plan}", response_model=PlanOut)
def obtener_plan_por_id(
    id_plan: int,
    session: Session = Depends(get_session)
):
    plan = session.get(Plan, id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return PlanOut.from_orm(plan)