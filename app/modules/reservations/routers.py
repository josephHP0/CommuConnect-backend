from datetime import datetime, date
from typing import List
from fastapi import HTTPException
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session
from app.core.db import get_session
from app.modules.services.models import Local
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
