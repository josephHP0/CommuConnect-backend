from sqlmodel import Session, select
from fastapi import HTTPException, UploadFile
from datetime import datetime
from app.modules.communities.models import Comunidad
import logging
import base64
from typing import Optional

from app.modules.services.models import ComunidadXServicio, Servicio
from app.modules.services.services import obtener_servicios_por_ids
from app.modules.services.schemas import ServicioOut

logger = logging.getLogger(__name__)

def eliminar_comunidad_service(id_comunidad: int, session: Session, current_admin_email: str):
    comunidad = session.exec(
        select(Comunidad).where(Comunidad.id_comunidad == id_comunidad, Comunidad.estado == True)
    ).first()

    if not comunidad:
        logger.warning(f"Comunidad con ID {id_comunidad} no encontrada o ya eliminada")
        raise HTTPException(status_code=404, detail="Comunidad no encontrada o ya eliminada")

    comunidad.estado = False
    comunidad.fecha_modificacion = datetime.utcnow()
    comunidad.modificado_por = current_admin_email

    session.add(comunidad)
    session.commit()

    logger.info(f"🗑️ Comunidad eliminada lógicamente: ID {id_comunidad} por {current_admin_email}")
    return {"mensaje": f"Comunidad ID {id_comunidad} eliminada correctamente"}

async def editar_comunidad_service(
    id_comunidad: int,
    nombre: Optional[str],
    slogan: Optional[str],
    imagen: Optional[UploadFile],
    session: Session,
    current_admin_email: str
):
    comunidad = session.exec(
        select(Comunidad).where(Comunidad.id_comunidad == id_comunidad, Comunidad.estado == True)
    ).first()

    if not comunidad:
        raise HTTPException(status_code=404, detail="Comunidad no encontrada o inactiva")

    if nombre is not None:
        comunidad.nombre = nombre

    if slogan is not None:
        comunidad.slogan = slogan

    if imagen is not None:
        comunidad.imagen = await imagen.read()

    comunidad.fecha_modificacion = datetime.utcnow()
    comunidad.modificado_por = current_admin_email

    session.add(comunidad)
    session.commit()
    session.refresh(comunidad)

    comunidad_dict = comunidad.__dict__.copy()
    if comunidad_dict.get("imagen"):
        comunidad_dict["imagen"] = base64.b64encode(comunidad_dict["imagen"]).decode("utf-8")

    return comunidad_dict

def register_user(user_data):
    # solo lo hice para que corra xd
    pass

def get_comunidades_con_servicios(session: Session):
    comunidades = session.exec(select(Comunidad)).all()
    servicios = session.exec(select(Servicio)).all()
    cxservicios = session.exec(select(ComunidadXServicio)).all()

    servicios_por_comunidad = {c.id_comunidad: [] for c in comunidades}
    servicios_dict = {s.id_servicio: s for s in servicios}
    for cx in cxservicios:
        if cx.id_comunidad in servicios_por_comunidad and cx.id_servicio in servicios_dict:
            servicios_por_comunidad[cx.id_comunidad].append(servicios_dict[cx.id_servicio])

    resultado = []
    for c in comunidades:
        comunidad_dict = c.dict()
        # Codifica imagen a base64 si existe
        if comunidad_dict.get("imagen"):
            comunidad_dict["imagen"] = base64.b64encode(comunidad_dict["imagen"]).decode("utf-8")
        # Haz lo mismo para los servicios
        servicios_list = []
        for s in servicios_por_comunidad[c.id_comunidad]:
            s_dict = s.dict()
            if s_dict.get("imagen"):
                s_dict["imagen"] = base64.b64encode(s_dict["imagen"]).decode("utf-8")
            servicios_list.append(s_dict)
        comunidad_dict["servicios"] = servicios_list
        resultado.append(comunidad_dict)
    return resultado


def get_comunidades_con_servicios_sin_imagen(session: Session):
    comunidades = session.exec(select(Comunidad)).all()
    servicios = session.exec(select(Servicio)).all()
    cxservicios = session.exec(select(ComunidadXServicio)).all()

    servicios_por_comunidad = {c.id_comunidad: [] for c in comunidades}
    servicios_dict = {s.id_servicio: s for s in servicios}
    for cx in cxservicios:
        if cx.id_comunidad in servicios_por_comunidad and cx.id_servicio in servicios_dict:
            servicios_por_comunidad[cx.id_comunidad].append(servicios_dict[cx.id_servicio])

    resultado = []
    for c in comunidades:
        comunidad_dict = c.dict()
        comunidad_dict.pop("imagen", None)  # Elimina imagen
        servicios_list = []
        for s in servicios_por_comunidad[c.id_comunidad]:
            s_dict = s.dict()
            s_dict.pop("imagen", None)  # Elimina imagen
            servicios_list.append(s_dict)
        comunidad_dict["servicios"] = servicios_list
        resultado.append(comunidad_dict)
    return resultado

def unir_cliente_a_comunidad(session: Session, id_cliente: int, id_comunidad: int):
    from app.modules.communities.models import ClienteXComunidad
    # Verifica si ya existe la relación
    existe = session.exec(
        select(ClienteXComunidad).where(
            ClienteXComunidad.id_cliente == id_cliente,
            ClienteXComunidad.id_comunidad == id_comunidad
        )
    ).first()
    if existe:
        return {"detail": "El cliente ya está unido a la comunidad."}
    # Si no existe, la crea
    relacion = ClienteXComunidad(id_cliente=id_cliente, id_comunidad=id_comunidad)
    session.add(relacion)
    session.commit()
    return {"detail": "Cliente unido a la comunidad exitosamente."}

def obtener_servicios_de_comunidad(session: Session, id_comunidad: int):
    servicio_ids = session.exec(
        select(ComunidadXServicio.id_servicio).where(
            ComunidadXServicio.id_comunidad == id_comunidad
        )
    ).all()

    return obtener_servicios_por_ids(session, servicio_ids) # type: ignore

def obtener_comunidad_por_id(session: Session, id_comunidad: int):
    comunidad = session.exec(
        select(Comunidad).where(Comunidad.id_comunidad == id_comunidad, Comunidad.estado == True)
    ).first()

    if not comunidad:
        raise HTTPException(status_code=404, detail="Comunidad no encontrada o inactiva")

    comunidad_dict = comunidad.dict()
    if comunidad_dict.get("imagen"):
        comunidad_dict["imagen"] = base64.b64encode(comunidad_dict["imagen"]).decode("utf-8")

    return comunidad_dict



def obtener_comunidad_con_imagen_base64(session: Session, id_comunidad: int):
    comunidad = session.exec(
        select(Comunidad).where(
            Comunidad.id_comunidad == id_comunidad,
            Comunidad.estado == True
        )
    ).first()

    if not comunidad:
        raise HTTPException(status_code=404, detail="Comunidad no encontrada")

    imagen_base64 = base64.b64encode(comunidad.imagen).decode("utf-8") if comunidad.imagen else None

    return comunidad, imagen_base64


def obtener_servicios_con_imagen_base64(session: Session, id_comunidad: int) -> list[ServicioOut]:
    servicios = obtener_servicios_de_comunidad(session, id_comunidad)
    servicios_out = []

    for servicio in servicios:
        imagen_base64 = (
            base64.b64encode(servicio.imagen).decode("utf-8")
            if servicio.imagen else None
        )

        servicio_out = ServicioOut(
            id_servicio=servicio.id_servicio, # type: ignore
            nombre=servicio.nombre,
            modalidad = servicio.modalidad,
            descripcion=servicio.descripcion,
            imagen=imagen_base64
        )

        servicios_out.append(servicio_out)

    return servicios_out
