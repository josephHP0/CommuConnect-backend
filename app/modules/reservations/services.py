from datetime import date, datetime, time, timedelta
from typing import List
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.modules.reservations.models import Sesion, SesionPresencial, SesionVirtual, Reserva
from app.modules.services.models import Local
from app.modules.users.models import Cliente
from fastapi import HTTPException,status
from app.modules.reservations.models import Sesion, Reserva, SesionVirtual
from app.modules.billing.models      import Inscripcion
from sqlalchemy.exc import IntegrityError

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
    local_obj = session.get(Local, id_local)
    if not local_obj or local_obj.id_distrito != id_distrito:
        return None
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

    horas_iso: List[str] = []
    for t in horas_objeto:
        if isinstance(t, time) or isinstance(t, datetime):
            horas_iso.append(t.strftime("%H:%M:%S"))
        else:
            # Si viniera timedelta (p. ej. SQLite):
            total = int(t.total_seconds())
            h = total // 3600
            m = (total % 3600) // 60
            s = total % 60
            horas_iso.append(f"{h:02d}:{m:02d}")

    # 6) Devolver el JSON con la lista de strings “HH:MM:SS”
    return horas_iso

def listar_sesiones_presenciales_detalladas(
    session: Session,
    id_servicio: int,
    id_distrito: int,
    id_local: int,
    fecha_seleccionada: date,
    hora_inicio: str   # ej. "10:00"
):
    # 1) Validar el local…
    local_obj = session.get(Local, id_local)
    if not local_obj or local_obj.id_distrito != id_distrito:
        return None

    # 2) Parsear la hora y formatear a HH:MM:SS
    hora_dt = datetime.strptime(hora_inicio, "%H:%M").time()
    hora_str_mysql = hora_dt.strftime("%H:%M:%S")  # → "10:00:00"

    # 3) Hacer la consulta filtrando por fecha y luego por TIME()
    stmt = (
        select(
            Sesion.id_sesion,
            SesionPresencial.id_sesion_presencial,
            func.date(Sesion.inicio).label("fecha"),
            Sesion.inicio.label("dt_inicio"),
            Sesion.fin.label("dt_fin"),
            SesionPresencial.creado_por.label("responsable"),
            SesionPresencial.capacidad.label("vacantes_totales"),
            Local.nombre.label("ubicacion"),
        )
        .join(SesionPresencial, SesionPresencial.id_sesion == Sesion.id_sesion)
        .join(Local, Local.id_local == SesionPresencial.id_local)
        .where(
            Sesion.id_servicio      == id_servicio,
            Sesion.tipo             == "Presencial",
            func.date(Sesion.inicio)== fecha_seleccionada,
            func.time(Sesion.inicio)== hora_str_mysql,    # aquí MySQL TIME()
            SesionPresencial.id_local == id_local,
            Local.id_distrito       == id_distrito,
        )
    )

    rows = session.exec(stmt).all()
    resultado = []
    for (
        id_ses, id_ses_pres, fecha_sesion,
        dt_inicio, dt_fin,
        responsable, vac_tot, ubicacion
    ) in rows:
        # 4) contar confirmadas, calcular vacantes_libres…
        total_confirmadas = session.exec(
            select(func.count(Reserva.id_reserva))
            .where(
                Reserva.id_sesion      == id_ses,
                Reserva.estado_reserva == "confirmada"
            )
        ).one()
        vac_libres = vac_tot - total_confirmadas

        resultado.append({
            "id_sesion":           id_ses,
            "id_sesion_presencial":id_ses_pres,
            "fecha":               fecha_sesion,
            "ubicacion":           ubicacion,
            "responsable":         responsable,
            "hora_inicio":           dt_inicio.strftime("%H:%M"),
            "hora_fin":              dt_fin.strftime("%H:%M"),
            "vacantes_totales":    vac_tot,
            "vacantes_libres":     vac_libres,
        })

    return resultado

def obtener_fechas_inicio_por_profesional(db: Session, id_profesional: int):
    statement = (
        select(SesionVirtual)
        .where(SesionVirtual.id_profesional == id_profesional)
        .options(selectinload(SesionVirtual.sesion))
    )

    resultados = db.exec(statement).all()

    if not resultados:
        return None

    fechas_formateadas = [
        {
            "id_sesion_virtual": sv.id_sesion_virtual,
            "id_sesion": sv.sesion.id_sesion if sv.sesion else None,
            "dia": sv.sesion.inicio.strftime("%Y-%m-%d") if sv.sesion and sv.sesion.inicio else None,
            "hora": sv.sesion.inicio.strftime("%H:%M:%S") if sv.sesion and sv.sesion.inicio else None
        }
        for sv in resultados
        if sv.sesion and sv.sesion.inicio
    ]
    return fechas_formateadas

def existe_reserva_para_usuario(db: Session, id_sesion: int, id_usuario: int) -> bool:
    # Buscar cliente
    stmt_cliente = select(Cliente).where(Cliente.id_usuario == id_usuario)
    cliente = db.exec(stmt_cliente).first()

    if not cliente:
        print("❌ Cliente no encontrado para este usuario.")
        return False

    print(f"🔍 Verificando reserva para id_sesion={id_sesion}, id_cliente={cliente.id_cliente}")

    # Buscar reserva
    stmt_reserva = select(Reserva).where(
        Reserva.id_sesion == id_sesion,
        Reserva.id_cliente == cliente.id_cliente,
    )

    reserva = db.exec(stmt_reserva).first()

    if reserva:
        print(f"✅ Reserva encontrada: ID {reserva.id_reserva}")
    else:
        print("⚠️ No se encontró ninguna reserva activa.")

    return reserva is not None






def validar_sesion_existente(session: Session, id_sesion: int) -> Sesion:
    """
    Verifica que la sesión exista. Lanza 404 si no.
    """
    sesion = session.get(Sesion, id_sesion)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return sesion


def validar_sesion_no_reservada(session: Session, id_sesion: int) -> None:
    """
    Verifica que la sesión no tenga ya una reserva activa. Lanza 409 si existe.
    """
    reserva = session.exec(
        select(Reserva).where(
            Reserva.id_sesion == id_sesion,
            Reserva.estado_reserva == "Activa"
        )
    ).first()
    if reserva:
        raise HTTPException(
            status_code=409,
            detail="La sesión ya está reservada por otro cliente."
        )


def validar_cliente_sin_conflicto(
    session: Session,
    cliente_id: int,
    sesion_actual: Sesion
) -> None:
    """
    Verifica que el cliente no tenga otra sesión activa solapada en horario.
    Lanza 409 si existe cruce.
    """
    reservas_conflictivas = session.exec(
        select(Reserva)
        .join(Sesion, Reserva.id_sesion == Sesion.id_sesion)
        .where(
            Reserva.id_cliente == cliente_id,
            Reserva.estado_reserva == "Activa",
            Sesion.inicio < sesion_actual.fin,
            Sesion.fin > sesion_actual.inicio
        )
    ).all()
    if reservas_conflictivas:
        raise HTTPException(
            status_code=409,
            detail="Ya tienes otra sesión activa que se cruza con ese horario."
        )


def crear_reserva(
    session: Session,
    id_sesion: int,
    cliente_id: int
) -> Reserva:
    """
    Inserta una nueva reserva activa y retorna el objeto.
    """
    nueva = Reserva(
        id_sesion=id_sesion,
        id_cliente=cliente_id,
        estado_reserva="Activa"
    )
    session.add(nueva)
    session.flush()  # asegura que nueva.id_reserva esté poblado
    return nueva


def obtener_url_archivo_virtual(session: Session, id_sesion: int) -> str | None:
    """
    Retorna la URL de archivo asociada a una sesión virtual, si existe.
    """
    sv = session.exec(
        select(SesionVirtual).where(SesionVirtual.id_sesion == id_sesion)
    ).first()
    return sv.url_archivo if sv else None


def reservar_sesion(
    session: Session,
    id_sesion: int,
    cliente_id: int
) -> Reserva:
    """
    Servicio que bloquea la fila de Sesion, valida unicidad solo en Virtual,
    y crea la reserva, todo dentro de un SAVEPOINT (begin_nested).
    """
    try:
        # 1) Savepoint en lugar de nueva transacción
        with session.begin_nested():
            # SELECT FOR UPDATE bajo ese SAVEPOINT
            sesion = session.exec(
                select(Sesion)
                  .where(Sesion.id_sesion == id_sesion)
                  .with_for_update()
            ).one_or_none()
            if not sesion:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesión no encontrada.")

            # Solo para Virtual: validar que no haya reserva activa
            if sesion.tipo == "Virtual":
                existe = session.exec(
                    select(Reserva)
                      .where(
                          Reserva.id_sesion      == id_sesion,
                          Reserva.estado_reserva == "Activa"
                      )
                ).first()
                if existe:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        "Ya existe una reserva activa para esta sesión virtual."
                    )

            # Validación de conflictos horario
            validar_cliente_sin_conflicto(session, cliente_id, sesion)

            # Crear la reserva dentro del mismo SAVEPOINT
            reserva = Reserva(
                id_sesion      = id_sesion,
                id_cliente     = cliente_id,
                estado_reserva = "Activa"
            )
            session.add(reserva)
            session.flush()

        # 2) Al salir del begin_nested() hacemos release savepoint, pero la tx sigue abierta.
        # 3) Aquí no hay más excepciones: FastAPI/tu router hará el commit final.
        return reserva

    except HTTPException:
        # se revierte al salir del savepoint
        raise

    except IntegrityError:
        # por si tienes alguna unique constraint residual
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Error de concurrencia al procesar la reserva. Intenta nuevamente."
        )

    except Exception:
        session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error interno al crear la reserva."
        )
