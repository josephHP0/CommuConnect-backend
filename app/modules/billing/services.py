from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.enums import MetodoPago
from .models import Inscripcion, Pago, Plan

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
    return pago