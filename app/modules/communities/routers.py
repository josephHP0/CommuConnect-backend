from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.communities.models import Comunidad
from app.modules.communities.schemas import ComunidadCreate, ComunidadOut, ComunidadRead
from typing import List, Optional
from datetime import datetime
from app.modules.users.dependencies import get_current_admin
import base64
from app.core.logger import logger 

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

@router.get("/listar_comunidad", response_model=List[ComunidadRead])
def listar_comunidades(session: Session = Depends(get_session)):
    try:
        comunidades = session.exec(select(Comunidad).where(Comunidad.estado == True)).all()
        logger.info(f"📄 Se listaron {len(comunidades)} comunidades activas")
        return comunidades
    except Exception as e:
        logger.error(f"❌ Error al listar comunidades: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener comunidades")
