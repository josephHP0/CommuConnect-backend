from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from app.db import get_session
from app.models.comunidad import Comunidad
from app.schemas.comunidad import ComunidadCreate, ComunidadRead
from typing import List, Optional
from datetime import datetime
from app.dependencies.administrador import get_current_admin

router = APIRouter()
'''
@router.post("/", response_model=ComunidadRead)
def crear_comunidad(comunidad: ComunidadCreate, session: Session = Depends(get_session)):
    nueva_comunidad = Comunidad(
        nombre=comunidad.nombre,
        slogan=comunidad.slogan,
        imagen=comunidad.imagen,
        creado_por=comunidad.creado_por,
        fecha_creacion=datetime.utcnow(),
        estado=True
    )
    session.add(nueva_comunidad)
    session.commit()
    session.refresh(nueva_comunidad)
    return nueva_comunidad
'''

@router.post("/", response_model=ComunidadRead)
async def crear_comunidad(
    nombre: str = Form(...),
    slogan: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin),
):
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
    return nueva_comunidad

### Con esto, Angular tendrá que enviar el formulario como FormData para poder cargar las imagenes

@router.get("/", response_model=List[ComunidadRead])
def listar_comunidades(session: Session = Depends(get_session)):
    comunidades = session.exec(select(Comunidad).where(Comunidad.estado == True)).all()
    return comunidades
