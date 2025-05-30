import traceback
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.communities.models import Comunidad
from app.modules.communities.schemas import ComunidadOut, ComunidadRead
from typing import List, Optional
from datetime import datetime
from app.modules.users.dependencies import get_current_admin
import base64
from app.core.logger import logger 
from app.modules.communities.services import eliminar_comunidad_service, get_comunidades_con_servicios, get_comunidades_con_servicios_sin_imagen
from app.modules.communities.services import editar_comunidad_service

router = APIRouter()

@router.post("/crear_comunidad", response_model=ComunidadRead)
async def crear_comunidad(
    nombre: str = Form(...),
    slogan: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin),
):
    try:
        imagen_bytes = await imagen.read() if imagen else None

        nueva_comunidad = Comunidad(
            nombre=nombre,
            slogan=slogan,
            imagen=imagen_bytes,
            creado_por=current_admin.email,
            fecha_creacion=datetime.utcnow(),        
            modificado_por=current_admin.email,
            fecha_modificacion=datetime.utcnow(),
            estado=True
        )

        session.add(nueva_comunidad)
        session.commit()
        session.refresh(nueva_comunidad)

        logger.info(f"✅ Comunidad creada: '{nombre}' por {current_admin.email}")

        comunidad_dict = nueva_comunidad.__dict__.copy()

        if comunidad_dict.get("imagen"):
            comunidad_dict["imagen"] = base64.b64encode(comunidad_dict["imagen"]).decode("utf-8")

        return ComunidadOut(**comunidad_dict)

    except Exception as e:
        logger.error(f"❌ Error al crear comunidad '{nombre}' por {current_admin.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear comunidad")

#Endpoint para listar comunidades activas
@router.get("/listar_comunidad", response_model=List[ComunidadRead])
def listar_comunidades(session: Session = Depends(get_session)):
    try:
        comunidades = session.exec(select(Comunidad).where(Comunidad.estado == True)).all()
        response = [ComunidadRead.from_orm_with_base64(c) for c in comunidades]
        logger.info(f"📄 Se listaron {len(response)} comunidades activas")
        return response
    except Exception as e:
        logger.error(f"❌ Error al listar comunidades: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener comunidades")

from fastapi import HTTPException

@router.delete("/eliminar_comunidad/{id_comunidad}")
def eliminar_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin)
):
    try:
        return eliminar_comunidad_service(id_comunidad, session, current_admin.email)
    except HTTPException as e:
        raise e  # Re-lanza errores ya controlados como 404
    except Exception as e:
        # Captura errores inesperados y los loguea
        logger.error(f"❌ Error inesperado al eliminar comunidad {id_comunidad}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inesperado al eliminar comunidad")

@router.put("/editar_comunidad/{id_comunidad}")
async def editar_comunidad(
    id_comunidad: int,
    nombre: Optional[str] = Form(None),
    slogan: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin)
):
    try:
        comunidad_dict = await editar_comunidad_service(
            id_comunidad=id_comunidad,
            nombre=nombre,
            slogan=slogan,
            imagen=imagen,
            session=session,
            current_admin_email=current_admin.email
        )
        return ComunidadOut(**comunidad_dict)
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        logger.error(f"❌ Error al editar comunidad ID {id_comunidad}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al editar comunidad")

#Endpoint para llamar a las comunidades con sus servicios asociados  
@router.get("/comunidades-con-servicios")
def comunidades_con_servicios(session: Session = Depends(get_session)):
    return get_comunidades_con_servicios(session)

#Endpoint para llamar a las comunidades con sus servicios asociados, pero sin imagen
@router.get("/comunidades-con-servicios_sinImagen")
def comunidades_con_servicios_sinImagen(session: Session = Depends(get_session)):
    return get_comunidades_con_servicios_sin_imagen(session)
