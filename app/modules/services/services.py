from sqlmodel import Session, select
from app.modules.services.models import Servicio, Profesional
from app.modules.reservations.models import SesionVirtual,Sesion
from typing import List
from app.modules.geography.models import Distrito  # Modelo de geografía
from app.modules.services.models import Local      # Modelo Local dentro de services
from app.modules.services.schemas import DistritoOut  # Esquema de salida (DTO)
import base64

def obtener_servicios_por_ids(session: Session, servicio_ids: List[int]):
    if not servicio_ids:
        return []

    servicios = session.exec(
        select(Servicio).where(
            Servicio.id_servicio.in_(servicio_ids), # type: ignore
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


def obtener_distritos_por_servicio_service(session: Session, id_servicio: int) -> List[DistritoOut]:
    # Obtener locales activos
    locales = session.exec(
        select(Local).where(Local.id_servicio == id_servicio, Local.estado == 1)
    ).all()

    if not locales:
        return []

    distrito_ids = {local.id_distrito for local in locales if local.id_distrito is not None}

    distritos = session.exec(
        select(Distrito).where(Distrito.id_distrito.in_(distrito_ids))
    ).all()

    resultado = []
    for d in distritos:
        imagen = base64.b64encode(d.imagen).decode("utf-8") if d.imagen else None
        resultado.append(DistritoOut(
            id_distrito=d.id_distrito,
            nombre=d.nombre,
            imagen=imagen
        ))

    return resultado
