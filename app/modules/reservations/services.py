from datetime import date
from typing import List

from sqlmodel import Session, select
from sqlalchemy import func

from app.modules.reservations.models import Sesion, SesionPresencial
from app.modules.services.models import Local


def obtener_fechas_presenciales(
    session: Session,
    id_servicio: int,
    id_distrito: int,
    id_local: int
) -> List[date]:
    """
    Ejecuta la consulta a la base de datos y devuelve
    una lista de fechas (date) sin repetición, donde
    hay sesiones “Presencial” filtradas por servicio, distrito y local.
    """

    # 1) Validar internamente que el local existe y pertenece al distrito
    local_obj = session.get(Local, id_local)
    if not local_obj or local_obj.id_distrito != id_distrito:
        return []  # o podrías lanzar una excepción custom aquí

    # 2) Construir la consulta
    stmt = (
        select(func.date(Sesion.inicio).label("solo_fecha"))
        .join(SesionPresencial, SesionPresencial.id_sesion == Sesion.id_sesion)
        .join(Local, Local.id_local == SesionPresencial.id_local)
        .where(
            Sesion.id_servicio == id_servicio,
            Sesion.tipo == "Presencial",
            SesionPresencial.id_local == id_local,
            Local.id_distrito == id_distrito,
        )
        .distinct()
    )

    raw_results = session.exec(stmt).all()
    fechas = [(row[0] if isinstance(row, tuple) else row) for row in raw_results]
    fechas.sort()
    return fechas

def obtener_horas_presenciales(
    session: Session,
    id_servicio: int,
    id_distrito: int,
    id_local: int,
    fecha_seleccionada: date
) -> List[str]:
    """
    Devuelve una lista de horas (strings "HH:MM") en que hay sesiones presenciales
    del servicio `id_servicio`, para el local `id_local` que debe pertenecer al
    distrito `id_distrito`, y en la fecha `fecha_seleccionada`.
    """

    # 1) Validar que el local exista y pertenezca al distrito
    local_obj = session.get(Local, id_local)
    if not local_obj or local_obj.id_distrito != id_distrito:
        # En lugar de devolver [], podrías optar por lanzar excepción y que el router la traduzca a 404
        return []

    # 2) Armar la consulta para extraer la HORA de inicio de Sesion para esa fecha
    #
    #    - func.date(Sesion.inicio) extrae solo la fecha
    #    - func.time(Sesion.inicio) (o concatenación/func.hour+func.minute) extrae la hora
    #      exacta en formato HH:MM:SS. MySQL y la mayoría de DB soportan func.time()
    #
    stmt = (
        select(func.time(Sesion.inicio).label("solo_hora"))
        .join(
            SesionPresencial,
            SesionPresencial.id_sesion == Sesion.id_sesion
        )
        .join(
            Local,
            Local.id_local == SesionPresencial.id_local
        )
        .where(
            Sesion.id_servicio == id_servicio,
            Sesion.tipo == "Presencial",
            func.date(Sesion.inicio) == fecha_seleccionada,  # filtro por la fecha_entera
            SesionPresencial.id_local == id_local,
            Local.id_distrito == id_distrito,
        )
        .distinct()  # para que no se repitan varias sesiones en la misma hora exacta
    )

    raw_results = session.exec(stmt).all()
    # `raw_results` puede venir como [(time1,), (time2,), …] o [time1, time2, …]
    horas_objeto = [
        (row[0] if isinstance(row, tuple) else row) for row in raw_results
    ]

    # 3) Convertir cada objeto time (tipo datetime.time) a string "HH:MM"
    horas_str = [t.strftime("%H:%M") for t in horas_objeto]
    horas_str.sort()
    return horas_str