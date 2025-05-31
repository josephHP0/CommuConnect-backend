from sqlmodel import Session, select
from app.modules.services.models import Servicio
from typing import List

def obtener_servicios_por_ids(session: Session, servicio_ids: List[int]):
    if not servicio_ids:
        return []

    servicios = session.exec(
        select(Servicio).where(
            Servicio.id_servicio.in_(servicio_ids),
            Servicio.estado == True  # Solo servicios activos
        )
    ).all()

    return servicios

def register_user(user_data):
    # solo lo hice para que corra xd
    pass
