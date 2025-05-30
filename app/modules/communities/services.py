from sqlmodel import Session, select
from fastapi import HTTPException, UploadFile
from datetime import datetime
from app.modules.communities.models import Comunidad
import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)

def eliminar_comunidad_service(id_comunidad: int, session: Session, current_admin_email: str):
    comunidad = session.exec(
        select(Comunidad).where(Comunidad.id_comunidad == id_comunidad, Comunidad.estado == True)
    ).first()

    if not comunidad:
        logger.warning(f"⚠️ Comunidad con ID {id_comunidad} no encontrada o ya eliminada")
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
