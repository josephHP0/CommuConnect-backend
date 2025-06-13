from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_user
from app.modules.services.services import actualizar_servicio, crear_servicio, eliminar_servicio, listar_servicios, obtener_profesionales_por_servicio, obtener_servicio_por_id
from typing import List, Optional
from app.modules.services.schemas import ProfesionalRead, ServicioCreate, ServicioRead, ServicioUpdate
from app.modules.services.services import obtener_distritos_por_servicio_service
from app.modules.services.schemas import DistritoOut
from app.modules.services.models import Local
from app.modules.services.schemas import LocalOut
from app.modules.users.models import Usuario
router = APIRouter()

@router.get("/profesionales/{id_servicio}", response_model=List[ProfesionalRead])
def listar_profesionales_por_servicio(id_servicio: int, session: Session = Depends(get_session)):
    try:
        resultado = obtener_profesionales_por_servicio(session, id_servicio)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    
@router.get("/usuario/servicio/{id_servicio}/distritos", response_model=List[DistritoOut])
def obtener_distritos_por_servicio(
    id_servicio: int,
    session: Session = Depends(get_session)
):
    return obtener_distritos_por_servicio_service(session, id_servicio)


@router.get("/servicio/{id_servicio}/distrito/{id_distrito}/locales", response_model=List[LocalOut])
def obtener_locales_por_servicio_y_distrito(
    id_servicio: int,
    id_distrito: int,
    session: Session = Depends(get_session)
):
    query = select(Local).where(
        Local.id_servicio == id_servicio,
        Local.id_distrito == id_distrito,
        Local.estado == 1
    )

    locales = session.exec(query).all()

    if not locales:
        raise HTTPException(status_code=404, detail="No se encontraron locales activos para ese servicio y distrito.")

    return locales

@router.get("/servicios", response_model=list[ServicioRead])
def listar_todos_los_servicios(session: Session = Depends(get_session)):
    return listar_servicios(session)

@router.post("/servicios", response_model=ServicioRead)
def crear_servicio_endpoint(
    session: Session = Depends(get_session),
    nombre: str = Form(...),
    descripcion: str = Form(...),
    modalidad: str = Form(...),
    imagen: UploadFile = File(...)
):
    datos = ServicioCreate(nombre=nombre, descripcion=descripcion, modalidad=modalidad)
    nuevo_servicio = crear_servicio(session, datos, imagen)

    import base64
    imagen_base64 = (
        base64.b64encode(nuevo_servicio.imagen).decode("utf-8")
        if nuevo_servicio.imagen else None
    )

    return ServicioRead(
        id_servicio=nuevo_servicio.id_servicio,
        nombre=nuevo_servicio.nombre,
        descripcion=nuevo_servicio.descripcion,
        modalidad=nuevo_servicio.modalidad,
        imagen_base64=imagen_base64,
        fecha_creacion=nuevo_servicio.fecha_creacion,
        creado_por=nuevo_servicio.creado_por,
        fecha_modificacion=nuevo_servicio.fecha_modificacion,
        modificado_por=nuevo_servicio.modificado_por,
        estado=nuevo_servicio.estado
    )

@router.delete("/servicios/{id_servicio}", status_code=200)
def eliminar_servicio_endpoint(
    id_servicio: int,
    session: Session = Depends(get_session)
):
    eliminar_servicio(session, id_servicio)
    return JSONResponse(content={"mensaje": "Servicio eliminado correctamente"})

@router.put("/servicios/{id_servicio}", response_model=ServicioRead)
def actualizar_servicio_endpoint(
    id_servicio: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    nombre: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    modalidad: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None)
):
    datos = ServicioUpdate(nombre=nombre, descripcion=descripcion, modalidad=modalidad)
    servicio_actualizado = actualizar_servicio(
        db=session,
        id_servicio=id_servicio,
        datos=datos,
        imagen=imagen,
        usuario=current_user.email  # o current_user.username o .id
    )

    import base64
    imagen_base64 = (
        base64.b64encode(servicio_actualizado.imagen).decode("utf-8")
        if servicio_actualizado.imagen else None
    )

    return ServicioRead(
        id_servicio=servicio_actualizado.id_servicio,
        nombre=servicio_actualizado.nombre,
        descripcion=servicio_actualizado.descripcion,
        modalidad=servicio_actualizado.modalidad,
        imagen_base64=imagen_base64,
        fecha_creacion=servicio_actualizado.fecha_creacion,
        creado_por=servicio_actualizado.creado_por,
        fecha_modificacion=servicio_actualizado.fecha_modificacion,
        modificado_por=servicio_actualizado.modificado_por,
        estado=servicio_actualizado.estado
    )

@router.get("/servicios/{id_servicio}", response_model=ServicioRead)
def obtener_servicio_por_identificador(
    id_servicio: int,
    session: Session = Depends(get_session)
):
    return obtener_servicio_por_id(session, id_servicio)