from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select

from app.modules.communities.models import ClienteXComunidad, Comunidad, ComunidadXPlan
from .schemas import ComunidadXPlanCreate, DetalleInscripcionCreate
from datetime import datetime

from app.core.enums import MetodoPago
from .models import Inscripcion, Pago, Plan, DetalleInscripcion



def get_planes(session: Session):
    planes = session.exec(select(Plan)).all()
    # Solo devuelve los campos del schema PlanOut
    return [
        {
            "id_plan": p.id_plan,
            "titulo": p.titulo,
            "descripcion": p.descripcion,
            "topes": p.topes,
            "precio": p.precio
        }
        for p in planes
    ]

def crear_pago_pendiente(session: Session, id_plan: int, creado_por: str):
    plan = session.get(Plan, id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    pago = Pago(
        monto=plan.precio,
        fecha_pago=None,
        metodo_pago=None,
        creado_por=creado_por,
        estado=0
    )
    session.add(pago)
    session.commit()
    session.refresh(pago)
    return pago

def crear_inscripcion(
    session: Session,
    id_plan: Optional[int],
    id_comunidad: int,
    id_cliente: int,
    id_pago: Optional[int],
    creado_por: str
):
    from datetime import timedelta

    ahora = datetime.utcnow()
    hace_un_mes = ahora - timedelta(days=30)

    # Busca inscripción previa pendiente en el último mes (pendiente de plan o de pago)
    inscripcion_previa = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado.in_([2, 3]), # type: ignore
            Inscripcion.fecha_creacion >= hace_un_mes
        )
    ).first()

    # Busca inscripción previa ya pagada (activa)
    inscripcion_pagada = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 1
        )
    ).first()
    nuevo_estado = 0
    # Determina el nuevo estado según los datos recibidos
    if not id_plan and not id_pago:
        nuevo_estado = 2  # Pendiente de plan


    if inscripcion_previa:
        # Sobrescribe la inscripción pendiente
        inscripcion_previa.id_plan = id_plan
        inscripcion_previa.id_pago = id_pago
        inscripcion_previa.modificado_por = creado_por
        inscripcion_previa.fecha_modificacion = ahora
        inscripcion_previa.estado = 3
        session.add(inscripcion_previa)
        session.commit()
        session.refresh(inscripcion_previa)
        return inscripcion_previa
    elif inscripcion_pagada:
        # Crea nueva inscripción con el estado correspondiente
        inscripcion = Inscripcion(
            estado=nuevo_estado,
            id_plan=id_plan,
            id_comunidad=id_comunidad,
            id_cliente=id_cliente,
            id_pago=id_pago,
            creado_por=creado_por,
            fecha_creacion=ahora
        )
        session.add(inscripcion)
        session.commit()
        session.refresh(inscripcion)
        return inscripcion
    else:
        # No hay inscripción previa, crea nueva
        if not id_plan and not id_pago:
            nuevo_estado = 2  # Pendiente de plan
        elif id_pago:
            nuevo_estado = 3  # Pendiente de pago
        inscripcion = Inscripcion(
            estado=nuevo_estado,
            id_plan=id_plan,
            id_comunidad=id_comunidad,
            id_cliente=id_cliente,
            id_pago=id_pago,
            creado_por=creado_por,
            fecha_creacion=ahora
        )
        session.add(inscripcion)
        session.commit()
        session.refresh(inscripcion)
        return inscripcion

def pagar_pendiente(
    session: Session,
    id_cliente: int,
    id_comunidad: int,
    creado_por: str
):
    # Busca la inscripción pendiente de pago del cliente en la comunidad
    inscripcion = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 3  # Solo pendiente de pago
        )
    ).first()
    if not inscripcion or not inscripcion.id_pago:
        raise HTTPException(status_code=404, detail="No hay pago pendiente para esta comunidad, redirigase a la página de inscripción")

    # Busca el pago pendiente
    pago = session.get(Pago, inscripcion.id_pago)
    if not pago or pago.estado != 0:
        raise HTTPException(status_code=404, detail="No hay pago pendiente para esta comunidad")

    # Actualiza el pago
    pago.fecha_pago = datetime.utcnow()
    pago.metodo_pago = MetodoPago.Tarjeta
    pago.estado = 1  # Pagado
    pago.modificado_por = creado_por
    session.add(pago)
    session.commit()
    session.refresh(pago)

    # Cambia el estado de la inscripción a 1 (activa)
    inscripcion.estado = 1
    inscripcion.modificado_por = creado_por
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)

    # Registrar la relación solo si no existe ya
    existe_relacion = session.exec(
        select(ClienteXComunidad).where(
            ClienteXComunidad.id_cliente == id_cliente,
            ClienteXComunidad.id_comunidad == id_comunidad
        )
    ).first()
    if not existe_relacion:
        relacion = ClienteXComunidad(
            id_cliente=id_cliente,
            id_comunidad=id_comunidad
        )
        session.add(relacion)
        session.commit()
        session.refresh(relacion)

    # Registrar el detalle de la inscripción si el plan tiene topes y no existe detalle
    plan = session.get(Plan, inscripcion.id_plan)
    if plan and plan.topes is not None:
        detalle_existente = session.exec(
            select(DetalleInscripcion).where(
                DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
            )
        ).first()
        if not detalle_existente:
            crear_detalle_inscripcion(
                session=session,
                id_inscripcion=inscripcion.id_inscripcion,  # type: ignore
                creado_por=creado_por
            )

    return pago



def obtener_inscripcion_activa(session: Session, id_cliente: int, id_comunidad: int) -> Inscripcion:
    query = select(Inscripcion).where(
        Inscripcion.id_cliente == id_cliente,
        Inscripcion.id_comunidad == id_comunidad,
        Inscripcion.estado == 1  # Solo inscripciones activas
    )
    inscripcion = session.exec(query).first()

    if not inscripcion:
        raise HTTPException(
            status_code=404,
            detail="El cliente no tiene inscripción activa en esta comunidad"
        )

    return inscripcion


def es_plan_con_topes(session: Session, id_inscripcion: int) -> bool:
    query = select(DetalleInscripcion).where(
        DetalleInscripcion.id_inscripcion == id_inscripcion
    )
    resultado = session.exec(query).first()

    return resultado is not None

def obtener_detalle_topes(session: Session, id_inscripcion: int) -> dict:
    detalle = session.exec(
        select(DetalleInscripcion).where(
            DetalleInscripcion.id_inscripcion == id_inscripcion
        )
    ).first()

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el detalle de topes para esta inscripción"
        )

    return {
        "topes_disponibles": detalle.topes_disponibles,
        "topes_consumidos": detalle.topes_consumidos
    }


def crear_detalle_inscripcion(
    session: Session,
    id_inscripcion: int,
    creado_por: str
) -> DetalleInscripcion:
    from datetime import timedelta

    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    plan = session.get(Plan, inscripcion.id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    fecha_inicio = datetime.utcnow()
    # Si el id_plan es impar, fecha_fin en 1 año; si es par, en 1 mes
    if inscripcion.id_plan and inscripcion.id_plan % 2 == 1:
        fecha_fin = fecha_inicio + timedelta(days=365)
    else:
        fecha_fin = fecha_inicio + timedelta(days=30)

    detalle = DetalleInscripcion(
        id_inscripcion=id_inscripcion,
        fecha_registro=fecha_inicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        topes_disponibles=plan.topes,
        topes_consumidos=0,
        fecha_creacion=fecha_inicio,
        creado_por=creado_por,
        fecha_modificacion=None,
        modificado_por=None,
        estado=1
    )
    session.add(detalle)
    session.commit()
    session.refresh(detalle)
    return detalle


def tiene_membresia_asociada(
    session: Session,
    cliente_id: int
) -> bool:
    """
    Retorna True si el cliente tiene al menos una inscripción
    activa (estado = 1) en cualquier comunidad.
    """
    stmt = (
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == cliente_id,
            Inscripcion.estado == 1  # Solo activas
        )
    )
    return session.exec(stmt).first() is not None


def tiene_membresia_activa_en_comunidad(session: Session, cliente_id: int, id_comunidad: int) -> bool:
    inscripcion = session.exec(
        select(Inscripcion).where(
            Inscripcion.id_cliente == cliente_id,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 1  # Activa
        )
    ).first()

    return bool(inscripcion)


def tiene_topes_disponibles(session: Session, id_cliente: int, id_comunidad: int) -> bool:
    inscripcion = obtener_inscripcion_activa(session, id_cliente, id_comunidad)

    if not es_plan_con_topes(session, inscripcion.id_inscripcion): # type: ignore
        return True  # Plan ilimitado, puede reservar sin topes

    detalle = obtener_detalle_topes(session, inscripcion.id_inscripcion) # type: ignore
    return detalle["topes_disponibles"] > 0

def congelar_inscripcion(session: Session, id_inscripcion: int, modificado_por: str):
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    inscripcion.estado = 0  # Congelado
    inscripcion.modificado_por = modificado_por
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion

def reactivar_inscripcion(session: Session, id_inscripcion: int, modificado_por: str):
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    if inscripcion.estado != 0:
        raise HTTPException(status_code=400, detail="Solo se pueden reactivar inscripciones congeladas")
    inscripcion.estado = 1  # Activa
    inscripcion.modificado_por = modificado_por
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion

def obtener_planes_por_comunidad(db: Session, id_comunidad: int) -> list[Plan]:
    query = (
        select(Plan)
        .join(ComunidadXPlan, Plan.id_plan == ComunidadXPlan.id_plan)
        .where(ComunidadXPlan.id_comunidad == id_comunidad)
        .where(ComunidadXPlan.estado == 1)
        .where(Plan.estado == 1)
    )
    return db.exec(query).all()

def agregar_plan_a_comunidad_serv(
    db: Session,
    data: ComunidadXPlanCreate,
    creado_por: str
) -> ComunidadXPlan:

    # Validar si ya existe
    existe = db.exec(
        select(ComunidadXPlan).where(
            ComunidadXPlan.id_comunidad == data.id_comunidad,
            ComunidadXPlan.id_plan == data.id_plan
        )
    ).first()

    if existe:
        raise HTTPException(status_code=409, detail="El plan ya está asociado a esta comunidad.")

    nueva_relacion = ComunidadXPlan(
        id_comunidad=data.id_comunidad,
        id_plan=data.id_plan,
        fecha_creacion=datetime.utcnow(),
        creado_por=creado_por,
        estado=1
    )

    db.add(nueva_relacion)
    db.commit()
    db.refresh(nueva_relacion)
    return nueva_relacion

def obtener_planes_no_asociados(db: Session, id_comunidad: int) -> list[Plan]:
    # Subconsulta: obtener ids de planes ya asociados a la comunidad
    subquery = (
        select(ComunidadXPlan.id_plan)
        .where(ComunidadXPlan.id_comunidad == id_comunidad)
    )

    # Consulta principal: obtener planes cuyo id no está en la subconsulta
    query = (
        select(Plan)
        .where(Plan.id_plan.not_in(subquery))
        .where(Plan.estado == 1)  # solo planes activos, opcional
    )

    return db.exec(query).all()