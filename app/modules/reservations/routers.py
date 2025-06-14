from datetime import datetime, date
from typing import List
from fastapi import HTTPException
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path as FastPath
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.services.models import Local
from app.modules.reservations.services import obtener_fechas_presenciales, obtener_horas_presenciales, listar_sesiones_presenciales_detalladas,obtener_fechas_inicio_por_profesional,existe_reserva_para_usuario, obtener_resumen_reserva_presencial, crear_reserva_presencial, listar_reservas_usuario_comunidad_semana, get_reservation_details, cancelar_reserva_por_id
from app.modules.reservations.schemas import FechasPresencialesResponse, HorasPresencialesResponse, ListaSesionesPresencialesResponse, ReservaPresencialSummary, ReservaRequest, ListaReservasResponse, ListaReservasComunidadResponse, ReservaComunidadResponse, ReservaDetailScreenResponse, ReservaResponse
from app.modules.auth.dependencies import get_current_user  
from app.modules.reservations.schemas import ReservaCreate
from app.modules.reservations.models   import Sesion, Reserva, SesionVirtual
from app.modules.auth.dependencies import get_current_cliente_id
from sqlalchemy.exc import IntegrityError
from app.modules.users.models import Usuario
from fastapi import BackgroundTasks
from app.modules.billing.services import obtener_inscripcion_activa, es_plan_con_topes, obtener_detalle_topes
from app.modules.users.models import Cliente
from utils.datetime_utils import convert_utc_to_local
from app.modules.users.dependencies import get_current_user
from app.modules.reservations.services import reservar_sesion_virtual, obtener_url_archivo_virtual

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

    filas = listar_sesiones_presenciales_detalladas(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local,
        fecha_seleccionada=fecha_obj,
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

@router.post(
    "/virtual",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva virtual"
)
def create_reserva_virtual(
    reserva_in: ReservaCreate,
    session: Session = Depends(get_session),
    cliente_id: int = Depends(get_current_cliente_id),
    usuario: Usuario = Depends(get_current_user)
) -> ReservaResponse:
    """
    Crea una reserva para una sesión virtual.
    El frontend solo envía el id_sesion; el backend orquesta validaciones y retorna la reserva.
    """
    try:
        # 1) Llamamos al service, que solo añade y hace flush
        reserva = reservar_sesion_virtual(
            session, reserva_in.id_sesion, cliente_id, usuario.id_usuario,
            id_comunidad=reserva_in.id_comunidad )

        # 2) Si no hubo excepción, confirmamos la transacción
        session.commit()

        # 3) Ahora podemos seguir obteniendo datos relacionados
        url_archivo = obtener_url_archivo_virtual(session, reserva.id_sesion)

        return ReservaResponse(
            id_reserva=reserva.id_reserva,
            id_sesion=reserva.id_sesion,
            id_cliente=reserva.id_cliente,
            id_comunidad=reserva.id_comunidad, 
            estado_reserva=reserva.estado_reserva,
            fecha_reservada=reserva.fecha_reservada,
            url_archivo=url_archivo,
            fecha_creacion=reserva.fecha_creacion
        )

    except HTTPException:
        # Rollback de validaciones (404, 409, etc.)
        session.rollback()
        raise

    except IntegrityError:
        # Si detectas un IntegrityError inesperado
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de concurrencia al procesar la reserva. Intenta nuevamente."
        )

    except Exception:
        # Cualquier otro error
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear la reserva."
        )
    


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
    response_model=ReservaResponse,
    summary="Crea una nueva reserva para una sesión presencial",
    status_code=status.HTTP_201_CREATED,
)
def create_reserva_presencial(
    *,
    reserva_in: ReservaRequest,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    bg_tasks: BackgroundTasks,
):
    """
    Crea una nueva reserva para una sesión presencial.
    El cliente debe estar autenticado.
    Se descuenta un crédito del plan del cliente si aplica.
    """
    response, error = crear_reserva_presencial(
        db=session,
        id_sesion=reserva_in.id_sesion,
        id_usuario=current_user.id_usuario,
        bg_tasks=bg_tasks
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return response

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
    
    response_reservas = []
    for reserva in reservas_data:
        local_inicio = convert_utc_to_local(reserva.inicio)
        local_fin = convert_utc_to_local(reserva.fin)
        
        response_reservas.append(
            ReservaComunidadResponse(
                id_reserva=reserva.id_reserva,
                nombre_servicio=reserva.nombre_servicio,
                fecha=local_inicio.date() if local_inicio else None,
                hora_inicio=local_inicio.time() if local_inicio else None,
                hora_fin=local_fin.time() if local_fin else None
            )
        )
    
    return ListaReservasComunidadResponse(reservas=response_reservas)

@router.get(
    "/{id_reserva}/details",
    response_model=ReservaDetailScreenResponse,
    summary="Obtiene el detalle de una reserva para la pantalla de detalle",
)
def get_reservation_details_for_screen(
    id_reserva: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    details, error = get_reservation_details(
        db=session,
        id_reserva=id_reserva,
        id_usuario=current_user.id_usuario
    )
    if error:
        raise HTTPException(status_code=404, detail=error)
    return details

@router.patch("/{id_reserva}/cancel", status_code=200)
def cancel_reservation(
    id_reserva: int = FastPath(..., title="ID de la Reserva a cancelar", ge=1),
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cancela una reserva específica de un usuario.
    """
    id_usuario = current_user.id_usuario
    result = cancelar_reserva_por_id(db=db, id_reserva=id_reserva, id_usuario=id_usuario)
    return result
