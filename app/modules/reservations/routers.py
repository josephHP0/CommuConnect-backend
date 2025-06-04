from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session
from app.core.db import get_session
from app.modules.reservations.services import obtener_fechas_presenciales, obtener_horas_presenciales, listar_sesiones_presenciales_detalladas,obtener_fechas_inicio_por_profesional,existe_reserva_para_usuario
from app.modules.reservations.schemas import FechasPresencialesResponse, HorasPresencialesResponse, ListaSesionesPresencialesResponse
from app.modules.auth.dependencies import get_current_user  
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

    # Si quisiéramos distinguir “local no existe o no pertenece” de “no hay sesiones”,
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
    id_servicio: int = Query(..., description="ID del servicio a filtrar"),
    id_distrito: int = Query(..., description="ID del distrito a filtrar"),
    id_local: int = Query(..., description="ID del local a filtrar"),
    fecha: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    session: Session = Depends(get_session),
):
    """
    Retorna todas las horas (sin repetir) en que hay sesiones presenciales
    para el servicio `id_servicio`, en el distrito `id_distrito`, 
    local `id_local` y la fecha `fecha` (solo día/mes/año).
    """

    horas = obtener_horas_presenciales(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local,
        fecha_seleccionada=fecha
    )

    # Si el service devolvió lista vacía y queremos distinguir “local inválido” 
    # de “no hay sesiones a esa hora”, podríamos hacer:
    if horas == []:
        # Aquí asumimos que `[]` puede significar “local inválido” o “sin horas disponibles”.
        # Si quisieras un 404 distinto a “no hay sesiones”:
        #    raise HTTPException(404, "Local no existe o no pertenece al distrito")
        # Pero si simplemente quieres “¿no hay horas disponibles?”, devuelves [] sin error.
        pass

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
    fecha: date = Query(..., description="Fecha (YYYY-MM-DD)"),
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

    filas = listar_sesiones_presenciales_detalladas(
        session=session,
        id_servicio=id_servicio,
        id_distrito=id_distrito,
        id_local=id_local,
        fecha_seleccionada=fecha,
        hora_inicio=hora
    )

    # Si el service devolvió lista vacía, podemos distinguir dos casos:
    #   a) el local no existe o no pertenece al distrito → devolvemos 404
    #   b) el local existe pero no hay sesiones EXACTAS para esa fecha/hora → devolvemos [] pero 200 OK.
    #
    # Para separar ambos, el service podría retornar None en caso “Local inválido”.
    if filas == []:
        # Asumiremos que “[]” significa que no hay sesiones para esa combinación exacta.
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
        print(f"❌ Error inesperado: {e}")
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
        print(f"❌ Error al verificar reserva: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
