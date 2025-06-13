from datetime import datetime, date
from typing import List
from fastapi import HTTPException
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.services.models import Local
from app.modules.reservations.services import obtener_fechas_presenciales, obtener_horas_presenciales, listar_sesiones_presenciales_detalladas,obtener_fechas_inicio_por_profesional,existe_reserva_para_usuario, obtener_resumen_reserva_presencial, crear_reserva, listar_reservas_usuario_comunidad_semana
from app.modules.reservations.schemas import FechasPresencialesResponse, HorasPresencialesResponse, ListaSesionesPresencialesResponse, ReservaPresencialSummary, ReservaRequest, ReservaDetailResponse, ListaReservasResponse, ListaReservasComunidadResponse, ReservaComunidadResponse
from app.modules.auth.dependencies import get_current_user  
from app.modules.users.models import Usuario
from fastapi import BackgroundTasks
from app.modules.billing.services import obtener_inscripcion_activa, es_plan_con_topes, obtener_detalle_topes
from app.modules.users.models import Cliente

router = APIRouter()

@router.get(
    "/fechas-presenciales",
    response_model=FechasPresencialesResponse,
    summary="Fechas de sesiones presenciales sin repetirse",
)
def listar_fechas_presenciales(
    *,
    id_servicio: int = Query(..., description="ID del servicio a filtrar"),
    id_distrito: int = Query(..., description="ID del distrito a filtrar"),
    id_local: int = Query(..., description="ID del local a filtrar"),
    session: Session = Depends(get_session),
):
    # Llamamos al service para hacer la consulta y validación
    fechas = obtener_fechas_presenciales(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local
    )

    # Si quisiéramos distinguir "local no existe o no pertenece" de "no hay sesiones",
    # el service podría lanzar excepción en ese caso y aquí atraparla:
    if fechas is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El local no existe o no pertenece al distrito indicado"
        )

    return FechasPresencialesResponse(fechas=fechas)

@router.get(
    "/horas-presenciales",
    response_model=HorasPresencialesResponse,
    summary="Horas de sesiones presenciales para un servicio/local/fecha dado",
)
def listar_horas_presenciales(
    *,
    id_servicio: int = Query(..., description="ID del servicio"),
    id_distrito: int = Query(..., description="ID del distrito"),
    id_local: int = Query(..., description="ID del local"),
    fecha: str = Query(..., description="Fecha en formato DD/MM/YYYY (p.ej. 10/06/2025)"),
    session: Session = Depends(get_session),
):
    # 1) Convertir la cadena DD/MM/YYYY a date
    try:
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido para 'fecha'. Debe ser DD/MM/YYYY, por ejemplo: 10/06/2025."
        )

    # 2) Validar local/distrito
    local_obj = session.get(Local, id_local)
    if not local_obj or local_obj.id_distrito != id_distrito:
        raise HTTPException(status_code=404, detail="Local no encontrado en ese distrito.")

    # 3) Obtener la lista de horas (List[str])
    horas = obtener_horas_presenciales(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local,
        fecha_seleccionada=fecha_obj
    )

    return HorasPresencialesResponse(horas=horas)

@router.get(
    "/sesiones-presenciales",
    response_model=ListaSesionesPresencialesResponse,
    summary="Listado de sesiones presenciales detalladas para un servicio/local/fecha/hora dados",
)
def sesiones_presenciales_detalladas(
    *,
    id_servicio: int = Query(..., description="ID del servicio a filtrar"),
    id_distrito: int = Query(..., description="ID del distrito a filtrar"),
    id_local: int = Query(..., description="ID del local a filtrar"),
    fecha: str = Query(..., description="Fecha en formato DD/MM/YYYY (p.ej. 10/06/2025)"),
    hora: str  = Query(..., description="Hora de inicio (HH:MM)"),
    session: Session = Depends(get_session),
):
    """
    Retorna un JSON con todas las sesiones presenciales que cumplan:
      - id_servicio
      - distrito → local
      - fecha exacta
      - hora de inicio exacta

    Cada objeto contendrá:
      fecha, ubicacion, responsable, hora_inicio, hora_fin, vacantes_totales, vacantes_libres.
    """

    try:
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido para 'fecha'. Debe ser DD/MM/YYYY, por ejemplo: 10/06/2025."
        )

    fecha_iso = fecha_obj.strftime("%Y-%m-%d")

    filas = listar_sesiones_presenciales_detalladas(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local,
        fecha_seleccionada=fecha_iso,
        hora_inicio=hora
    )
    if filas is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El local no existe o no pertenece al distrito indicado"
        )

    if filas == []:
        # Asumiremos que "[]" significa que no hay sesiones para esa combinación exacta.
        # Si deseas un 404 cuando el local está mal, haz que el service devuelva 'None' en ese caso.
        return ListaSesionesPresencialesResponse(sesiones=[])

    return ListaSesionesPresencialesResponse(sesiones=filas)

@router.get("/fechas-sesiones_virtuales_por_profesional/{id_profesional}")
def get_fechas_sesiones(id_profesional: int, session: Session = Depends(get_session)):
    try:
        fechas = obtener_fechas_inicio_por_profesional(session, id_profesional)

        if not fechas:
            raise HTTPException(status_code=404, detail="No se encontraron sesiones virtuales.")

        return {"fechas_inicio": fechas}

    except Exception as e:
        print(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

@router.get("/reserva-existe/{id_sesion}")
def verificar_reserva(
    id_sesion: int,
    db: Session = Depends(get_session),
    usuario=Depends(get_current_user)
):
    try:
        id_usuario= usuario.id_usuario  # 🔧 usa el campo correcto aquí
        existe = existe_reserva_para_usuario(db, id_sesion, id_usuario)
        return {"reserva_existente": existe}
    except Exception as e:
        print(f"Error al verificar reserva: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

@router.get(
    "/summary/{id_sesion}",
    response_model=ReservaPresencialSummary,
    summary="Obtiene el resumen de una sesión presencial para el usuario actual",
)
def get_resumen_reserva_presencial(
    *,
    id_sesion: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    resumen, error = obtener_resumen_reserva_presencial(
        db=session, id_sesion=id_sesion, id_usuario=current_user.id_usuario
    )

    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return resumen

@router.post(
    "/",
    response_model=ReservaDetailResponse,
    summary="Crea una nueva reserva para una sesión",
    status_code=status.HTTP_201_CREATED,
)
def create_new_reservation(
    *,
    reserva_in: ReservaRequest,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    bg_tasks: BackgroundTasks,
):
    reserva, error = crear_reserva(
        db=session,
        id_sesion=reserva_in.id_sesion,
        id_usuario=current_user.id_usuario,
        bg_tasks=bg_tasks,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return reserva

@router.get(
    "/by-user-community",
    response_model=ListaReservasComunidadResponse,
    summary="Listar reservas de un usuario en una comunidad para los siguientes 7 dias",
)
def list_reservations_by_user_community(
    *,
    id_comunidad: int = Query(..., description="ID de la comunidad a filtrar"),
    fecha: str = Query(..., description="Fecha de inicio en formato DD/MM/YYYY"),
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido para 'fecha'. Debe ser DD/MM/YYYY."
        )

    reservas_data = listar_reservas_usuario_comunidad_semana(
        db=session, 
        id_usuario=current_user.id_usuario, 
        id_comunidad=id_comunidad, 
        fecha=fecha_obj
    )
    
    response_reservas = [
        ReservaComunidadResponse(
            id_reserva=reserva.id_reserva,
            nombre_servicio=reserva.nombre_servicio,
            fecha=reserva.inicio.date(),
            hora_inicio=reserva.inicio.time(),
            hora_fin=reserva.fin.time()
        ) for reserva in reservas_data
    ]
    
    return ListaReservasComunidadResponse(reservas=response_reservas)
