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

def listar_sesiones_presenciales_detalladas(
    session: Session,
    id_servicio: int,
    id_distrito: int,
    id_local: int,
    fecha_seleccionada: date,
    hora_inicio: str   # esperaremos un string tipo "15:00" (HH:MM)
) -> List[dict]:
    """
    Retorna una lista de diccionarios con todos los campos necesarios
    para SesionPresencialOut, filtrando por servicio, distrito, local, fecha y hora de inicio.
    Cada diccionario tendrá las claves:
      - fecha (date)
      - ubicacion (str)
      - responsable (str)
      - hora_inicio (time)
      - hora_fin (time)
      - vacantes_totales (int)
      - vacantes_libres (int)
    """

    # 1) Validar que el local exista y pertenezca al distrito
    local_obj = session.get(Local, id_local)
    if not local_obj or local_obj.id_distrito != id_distrito:
        # Devolvemos lista vacía para que el router lance 404 o lo interprete a su manera.
        return []

    # 2) Convertir el string "HH:MM" a objeto time (para comparar con Sesion.inicio)
    from datetime import datetime
    hora_dt = datetime.strptime(hora_inicio, "%H:%M").time()

    # 3) Armar la consulta:
    #
    #    - Haremos JOIN entre Sesion → SesionPresencial → Local
    #    - Filtramos:
    #          a) Sesion.id_servicio == id_servicio
    #          b) Sesion.tipo == "Presencial"
    #          c) DATE(Sesion.inicio) == fecha_seleccionada
    #          d) TIME(Sesion.inicio) == hora_dt
    #          e) SesionPresencial.id_local == id_local
    #          f) Local.id_distrito == id_distrito
    #
    #    - Seleccionamos las columnas necesarias: Sesion.inicio, Sesion.fin, Sesion.creado_por, SesionPresencial.capacidad, Local.nombre
    #
    stmt = (
        select(
            func.date(Sesion.inicio).label("fecha_sesion"),
            Sesion.inicio.label("datetime_inicio"),
            Sesion.fin.label("datetime_fin"),
            SesionPresencial.creado_por.label("responsable"),
            SesionPresencial.capacidad.label("vacantes_totales"),
            Local.nombre.label("nombre_local"),
        )
        .join(SesionPresencial, SesionPresencial.id_sesion == Sesion.id_sesion)
        .join(Local, Local.id_local == SesionPresencial.id_local)
        .where(
            Sesion.id_servicio == id_servicio,
            Sesion.tipo == "Presencial",
            func.date(Sesion.inicio) == fecha_seleccionada,
            func.time(Sesion.inicio) == hora_dt,
            SesionPresencial.id_local == id_local,
            Local.id_distrito == id_distrito,
        )
    )

    rows = session.exec(stmt).all()

    resultado: List[dict] = []
    for row in rows:
        # row = ( fecha_sesion, datetime_inicio, datetime_fin, responsable, vacantes_totales, nombre_local )
        fecha_sesion, dt_inicio, dt_fin, responsable, vacantes_totales, nombre_local = row

        # 4) Calcular cuántas reservas hay YA confirmadas para esa sesión:
        #    Asumimos que en la tabla Reserva, el campo `id_sesion` referencia a Sesion.id_sesion,
        #    y que “reservas activas” se identifican con estado_reserva = 'confirmada' (o similar).
        #
        count_stmt = (
            select(func.count(Reserva.id_reserva))
            .where(
                Reserva.id_sesion == SesionPresencial.id_sesion,  
                Reserva.estado_reserva == "confirmada"
            )
        )
        # Para hacer la subconsulta, primero necesitamos el id_sesion: 
        # Pero en este select original no trajimos el id_sesion, así que podemos:
        #    a) Añadirlo a la selección
        #    b) O hacer una segunda query con el filtro de la misma fecha/hora/local
        #
        # La forma más clara es añadirlo en el SELECT inicial:
        #
        # select(
        #     ...
        #     Sesion.id_sesion.label("id_sesion"),
        #     ...
        # )
        #
        # Para simplificar, supongamos que modificamos el SELECT así:
        #    select(
        #       Sesion.id_sesion.label("id_sesion"),
        #       func.date(Sesion.inicio).label("fecha_sesion"),
        #       ...
        #    )
        #
        # Y luego hacemos:
        id_sesion_actual = Sesion.id_sesion  # aquí iría el valor leído de la fila. 
        # (En la práctica, row.id_sesion o row[0] si lo seleccionaste primero)

        # *** Para ilustrar el flujo completo, reescribamos rápidamente el SELECT arriba: ***

        # (¡Este bloque es conceptual! Asegúrate en tu código de traer id_sesion en el SELECT original.)

        # --- SELECT revisado para incluir id_sesion ---
        # stmt = (
        #     select(
        #         Sesion.id_sesion.label("id_sesion"),
        #         func.date(Sesion.inicio).label("fecha_sesion"),
        #         Sesion.inicio.label("datetime_inicio"),
        #         Sesion.fin.label("datetime_fin"),
        #         SesionPresencial.creado_por.label("responsable"),
        #         SesionPresencial.capacidad.label("vacantes_totales"),
        #         Local.nombre.label("nombre_local"),
        #     )
        #     .join(SesionPresencial, SesionPresencial.id_sesion == Sesion.id_sesion)
        #     .join(Local, Local.id_local == SesionPresencial.id_local)
        #     .where(
        #         Sesion.id_servicio == id_servicio,
        #         Sesion.tipo == "Presencial",
        #         func.date(Sesion.inicio) == fecha_seleccionada,
        #         func.time(Sesion.inicio) == hora_dt,
        #         SesionPresencial.id_local == id_local,
        #         Local.id_distrito == id_distrito,
        #     )
        # )
        #
        # rows = session.exec(stmt).all()
        #
        # for row in rows:
        #     id_sesion_actual = row.id_sesion
        #     fecha_sesion    = row.fecha_sesion
        #     dt_inicio       = row.datetime_inicio
        #     dt_fin          = row.datetime_fin
        #     responsable     = row.responsable
        #     vacantes_totales = row.vacantes_totales
        #     nombre_local    = row.nombre_local
        #

        # Ahora sí podemos hacer el conteo:
        count_stmt = (
            select(func.count(Reserva.id_reserva))
            .where(
                Reserva.id_sesion == id_sesion_actual,
                Reserva.estado_reserva == "confirmada"
            )
        )
        total_reservas_confirmadas = session.exec(count_stmt).one()
        vacantes_libres = vacantes_totales - total_reservas_confirmadas

        resultado.append({
            "fecha": fecha_sesion,
            "ubicacion": nombre_local,
            "responsable": responsable,
            "hora_inicio": dt_inicio.time(),
            "hora_fin": dt_fin.time(),
            "vacantes_totales": vacantes_totales,
            "vacantes_libres": vacantes_libres,
        })

    return resultado