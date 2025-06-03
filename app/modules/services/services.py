from sqlmodel import Session, select
from app.modules.services.models import Servicio, Profesional
from app.modules.reservations.models import SesionVirtual,Sesion
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


def obtener_profesionales_por_servicio(session: Session, id_servicio: int):
    """
    Recupera todos los profesionales cuyo campo `id_servicio` coincide con el parámetro.
    Previamente, esta función buscaba a través de Sesion → SesionVirtual, pero como
    ahora `Profesional` lleva directamente `id_servicio`, podemos simplificar la consulta.
    """
    profesionales = session.exec(
        select(Profesional).where(Profesional.id_servicio == id_servicio)
    ).all()
    return profesionales

