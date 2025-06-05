from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select
from .schemas import DetalleInscripcionCreate
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
    inscripcion = Inscripcion(
        id_plan=id_plan,
        id_comunidad=id_comunidad,
        id_cliente=id_cliente,
        id_pago=id_pago,
        creado_por=creado_por,
        estado=1  # o el valor que corresponda
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
    # Busca la inscripción activa del cliente en la comunidad
    inscripcion = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad
        )
    ).first()
    if not inscripcion or not inscripcion.id_pago:
        raise HTTPException(status_code=404, detail="No hay pago pendiente para esta comunidad")

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

    # Registrar el detalle de la inscripción si el plan tiene topes y no existe detalle
    plan = session.get(Plan, inscripcion.id_plan)
    if plan and plan.topes is not None:
        detalle_existente = session.exec(
            select(DetalleInscripcion).where(
                DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
            )
        ).first()
        if not detalle_existente:
            detalle = DetalleInscripcion(
                id_inscripcion=inscripcion.id_inscripcion, # type: ignore
                fecha_registro=datetime.utcnow(),
                fecha_inicio=datetime.utcnow(),
                fecha_fin=None,
                topes_disponibles=plan.topes,
                topes_consumidos=0,
                fecha_creacion=datetime.utcnow(),
                creado_por=creado_por,
                fecha_modificacion=None,
                modificado_por=None,
                estado=1
            )
            session.add(detalle)
            session.commit()
            session.refresh(detalle)

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
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    plan = session.get(Plan, inscripcion.id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    detalle = DetalleInscripcion(
        id_inscripcion=id_inscripcion,
        fecha_registro=datetime.utcnow(),
        fecha_inicio=datetime.utcnow(),
        fecha_fin=None,
        topes_disponibles=plan.topes,
        topes_consumidos=0,
        fecha_creacion=datetime.utcnow(),
        creado_por=creado_por,
        fecha_modificacion=None,
        modificado_por=None,
        estado=1
    )
    session.add(detalle)
    session.commit()
    session.refresh(detalle)
    return detalle