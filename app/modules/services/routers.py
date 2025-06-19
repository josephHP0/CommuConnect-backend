from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_user
from app.modules.users.dependencies import get_current_admin
from app.modules.services.services import actualizar_servicio, crear_profesional, crear_servicio, eliminar_servicio, listar_locales_por_servicio, listar_profesionales, listar_servicios, obtener_profesionales_por_servicio, obtener_servicio_por_id
from typing import List, Optional
from app.modules.services.schemas import ProfesionalRead, ServicioCreate, ServicioRead, ServicioUpdate, ServicioOut
from app.modules.services.services import obtener_distritos_por_servicio_service
from app.modules.services.schemas import DistritoOut
from app.modules.services.models import Local
from app.modules.services.schemas import ProfesionalCreate, ProfesionalOut
from app.modules.services.schemas import LocalOut
from app.modules.users.models import Usuario
from app.modules.communities.services import obtener_servicios_con_imagen_base64
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

@router.get("/", response_model=list[ProfesionalOut])
def obtener_profesionales(db: Session = Depends(get_session)):
    return listar_profesionales(db)

@router.post("/", response_model=ProfesionalOut)
def registrar_profesional_con_servicio(
    data: ProfesionalCreate,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return crear_profesional(db, data, creado_por=current_user.email)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/por-servicio/{id_servicio}", response_model=list[LocalOut])
def obtener_locales_por_servicio(id_servicio: int, db: Session = Depends(get_session)):
    locales = listar_locales_por_servicio(db, id_servicio)
    if not locales:
        raise HTTPException(status_code=404, detail="No se encontraron locales para este servicio")
    return locales



@router.get("/admin/comunidad/{id_comunidad}/servicios", response_model=List[ServicioOut])
def listar_servicios_por_comunidad_admin(
    id_comunidad: int,
    session: Session = Depends(get_session),
    current_admin: Usuario = Depends(get_current_admin)
):
    """
    Endpoint para administradores: Lista todos los servicios asociados a una comunidad específica.
    """
    try:
        servicios = obtener_servicios_con_imagen_base64(session, id_comunidad)
        return servicios
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al obtener servicios de la comunidad: {str(e)}"
        )

@router.patch("/admin/comunidad/{id_comunidad}/servicio/{id_servicio}/estado")
def cambiar_estado_servicio_comunidad(
    id_comunidad: int,
    id_servicio: int,
    estado: int = Query(..., description="Nuevo estado: 1=Activo, 0=Inactivo"),
    session: Session = Depends(get_session),
    current_admin: Usuario = Depends(get_current_admin)
):
    """
    Endpoint para administradores: Activa o desactiva un servicio en una comunidad específica.
    """
    # Validar que el estado sea válido
    if estado not in [0, 1]:
        raise HTTPException(
            status_code=400, 
            detail="Estado debe ser 0 (inactivo) o 1 (activo)"
        )
    
    # Buscar la relación comunidad-servicio
    from app.modules.services.models import ComunidadXServicio
    relacion = session.exec(
        select(ComunidadXServicio).where(
            ComunidadXServicio.id_comunidad == id_comunidad,
            ComunidadXServicio.id_servicio == id_servicio
        )
    ).first()
    
    if not relacion:
        raise HTTPException(
            status_code=404, 
            detail=f"No existe relación entre la comunidad {id_comunidad} y el servicio {id_servicio}"
        )
    
    # Actualizar el estado
    estado_anterior = relacion.estado
    relacion.estado = estado
    session.add(relacion)
    session.commit()
    
    accion = "activado" if estado == 1 else "desactivado"
    
    return {
        "mensaje": f"Servicio {accion} exitosamente en la comunidad",
        "id_comunidad": id_comunidad,
        "id_servicio": id_servicio,
        "estado_anterior": estado_anterior,
        "estado_nuevo": estado,
        "modificado_por": current_admin.email
    }

@router.get("/admin/comunidad/{id_comunidad}/servicios-disponibles", response_model=List[ServicioOut])
def listar_servicios_disponibles_para_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    current_admin: Usuario = Depends(get_current_admin)
):
    """
    Endpoint para administradores: Lista todos los servicios que NO están en la comunidad 
    o que están desactivados (estado = 0).
    """
    try:
        # Obtener todos los servicios activos
        from app.modules.services.models import Servicio
        servicios_activos = session.exec(
            select(Servicio).where(Servicio.estado == True)
        ).all()
        
        # Obtener servicios ya asociados y ACTIVOS en la comunidad
        from app.modules.services.models import ComunidadXServicio
        servicios_asociados_activos_query = session.exec(
            select(ComunidadXServicio.id_servicio).where(
                ComunidadXServicio.id_comunidad == id_comunidad,
                ComunidadXServicio.estado == 1
            )
        )
        servicios_asociados_activos = [id_servicio for id_servicio in servicios_asociados_activos_query]
        
        # Filtrar servicios disponibles (no asociados o desactivados)
        servicios_disponibles = []
        for servicio in servicios_activos:
            if servicio.id_servicio not in servicios_asociados_activos:
                # Convertir imagen a base64 si existe
                import base64
                imagen_base64 = (
                    base64.b64encode(servicio.imagen).decode("utf-8")
                    if servicio.imagen else None
                )
                
                servicio_out = ServicioOut(
                    id_servicio=servicio.id_servicio,
                    nombre=servicio.nombre,
                    modalidad=servicio.modalidad,
                    descripcion=servicio.descripcion,
                    imagen=imagen_base64
                )
                servicios_disponibles.append(servicio_out)
        
        return servicios_disponibles
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al obtener servicios disponibles: {str(e)}"
        )

@router.post("/admin/comunidad/{id_comunidad}/servicio/{id_servicio}/añadir")
def añadir_servicio_a_comunidad(
    id_comunidad: int,
    id_servicio: int,
    session: Session = Depends(get_session),
    current_admin: Usuario = Depends(get_current_admin)
):
    """
    Endpoint para administradores: Añade un servicio a una comunidad.
    Si la relación ya existe pero está desactivada, la activa.
    Si no existe, crea una nueva relación activa.
    """
    try:
        # Verificar que la comunidad existe
        from app.modules.communities.models import Comunidad
        comunidad = session.get(Comunidad, id_comunidad)
        if not comunidad or not comunidad.estado:
            raise HTTPException(status_code=404, detail="Comunidad no encontrada o inactiva")
        
        # Verificar que el servicio existe y está activo
        from app.modules.services.models import Servicio
        servicio = session.get(Servicio, id_servicio)
        if not servicio or not servicio.estado:
            raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo")
        
        # Buscar si ya existe la relación
        from app.modules.services.models import ComunidadXServicio
        relacion_existente = session.exec(
            select(ComunidadXServicio).where(
                ComunidadXServicio.id_comunidad == id_comunidad,
                ComunidadXServicio.id_servicio == id_servicio
            )
        ).first()
        
        if relacion_existente:
            if relacion_existente.estado == 1:
                return {
                    "mensaje": "El servicio ya está activo en esta comunidad",
                    "id_comunidad": id_comunidad,
                    "id_servicio": id_servicio,
                    "nombre_servicio": servicio.nombre,
                    "nombre_comunidad": comunidad.nombre,
                    "accion": "ya_existe",
                    "estado": 1
                }
            else:
                # Activar relación existente
                relacion_existente.estado = 1
                session.add(relacion_existente)
                session.commit()
                
                return {
                    "mensaje": "Servicio reactivado exitosamente en la comunidad",
                    "id_comunidad": id_comunidad,
                    "id_servicio": id_servicio,
                    "nombre_servicio": servicio.nombre,
                    "nombre_comunidad": comunidad.nombre,
                    "accion": "reactivado",
                    "estado": 1
                }
        else:
            # Crear nueva relación
            nueva_relacion = ComunidadXServicio(
                id_comunidad=id_comunidad,
                id_servicio=id_servicio,
                estado=1
            )
            session.add(nueva_relacion)
            session.commit()
            
            return {
                "mensaje": "Servicio añadido exitosamente a la comunidad",
                "id_comunidad": id_comunidad,
                "id_servicio": id_servicio,
                "nombre_servicio": servicio.nombre,
                "nombre_comunidad": comunidad.nombre,
                "accion": "creado",
                "estado": 1
            }
            
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al añadir servicio: {str(e)}"
        )