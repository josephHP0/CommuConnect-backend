from datetime import date, datetime, time, timedelta
from typing import List
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.modules.reservations.models import Sesion, SesionPresencial, SesionVirtual, Reserva
from app.modules.services.models import Local, Servicio, ComunidadXServicio
from app.modules.users.models import Cliente, Usuario
from app.modules.billing.services import (
    obtener_inscripcion_activa, 
    es_plan_con_topes, 
    obtener_detalle_topes
)
from app.modules.billing.models import DetalleInscripcion
from utils.email_brevo import send_reservation_email
from fastapi import BackgroundTasks
from app.modules.communities.models import Comunidad

def listar_reservas_usuario_comunidad_semana(db: Session, id_usuario: int, id_comunidad: int, fecha: date):
    end_date = fecha + timedelta(days=7)

    cliente = db.exec(select(Cliente).where(Cliente.id_usuario == id_usuario)).first()
    if not cliente:
        return []

    stmt = (
        select(
            Reserva.id_reserva,
            Servicio.nombre.label("nombre_servicio"),
            Sesion.inicio,
            Sesion.fin
        )
        .join(Sesion, Reserva.id_sesion == Sesion.id_sesion)
        .join(Servicio, Sesion.id_servicio == Servicio.id_servicio)
        .join(ComunidadXServicio, Servicio.id_servicio == ComunidadXServicio.id_servicio)
        .where(Reserva.id_cliente == cliente.id_cliente)
        .where(ComunidadXServicio.id_comunidad == id_comunidad)
        .where(func.date(Sesion.inicio) >= fecha)
        .where(func.date(Sesion.inicio) < end_date)
    )
    
    reservas = db.exec(stmt).all()
    return reservas

def obtener_fechas_presenciales(
    session: Session,
    id_servicio: int,
    id_distrito: int,
    id_local: int
) -> List[date]:
    """
    Ejecuta la consulta a la base de datos y devuelve
    una lista de fechas (date) sin repetición, donde
    hay sesiones "Presencial" filtradas por servicio, distrito y local.
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

    # 6) Devolver el JSON con la lista de strings "HH:MM:SS"
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
        print("Cliente no encontrado para este usuario.")
        return False

    print(f"🔍 Verificando reserva para id_sesion={id_sesion}, id_cliente={cliente.id_cliente}")

    # Buscar reserva
    stmt_reserva = select(Reserva).where(
        Reserva.id_sesion == id_sesion,
        Reserva.id_cliente == cliente.id_cliente,
    )

    reserva = db.exec(stmt_reserva).first()

    if reserva:
        print(f"Reserva encontrada: ID {reserva.id_reserva}")
    else:
        print("No se encontró ninguna reserva activa.")

    return reserva is not None

def obtener_resumen_reserva_presencial(db: Session, id_sesion: int, id_usuario: int):
    # 1. Obtener datos del usuario
    usuario = db.get(Usuario, id_usuario)
    if not usuario:
        return None, "Usuario no encontrado"

    # 2. Obtener datos de la sesión
    stmt = (
        select(
            Sesion.id_sesion,
            SesionPresencial.id_sesion_presencial,
            func.date(Sesion.inicio).label("fecha"),
            Sesion.inicio.label("dt_inicio"),
            Sesion.fin.label("dt_fin"),
            SesionPresencial.creado_por.label("responsable"),
            SesionPresencial.capacidad.label("vac_tot"),
            Local.nombre.label("ubicacion")
        )
        .join(SesionPresencial, SesionPresencial.id_sesion == Sesion.id_sesion)
        .join(Local, Local.id_local == SesionPresencial.id_local)
        .where(Sesion.id_sesion == id_sesion)
    )
    
    sesion_data = db.exec(stmt).first()

    if not sesion_data:
        return None, "Sesión no encontrada"
    
    (
        id_ses, id_ses_pres, fecha_sesion,
        dt_inicio, dt_fin,
        responsable, vac_tot, ubicacion
    ) = sesion_data


    resumen = {
        "id_sesion": id_ses,
        "id_sesion_presencial": id_ses_pres,
        "fecha": fecha_sesion,
        "ubicacion": ubicacion,
        "responsable": responsable,
        "hora_inicio": dt_inicio.strftime("%H:%M"),
        "hora_fin": dt_fin.strftime("%H:%M"),
        "vacantes_totales": vac_tot,
        "nombres": usuario.nombre,
        "apellidos": usuario.apellido
    }
    
    return resumen, None

def crear_reserva(db: Session, id_sesion: int, id_usuario: int, bg_tasks: BackgroundTasks):
    with db.begin_nested():
        # 1. Buscar el cliente y su usuario
        cliente = db.exec(select(Cliente).where(Cliente.id_usuario == id_usuario)).first()
        if not cliente:
            return None, "Cliente no encontrado"
        
        usuario = db.get(Usuario, id_usuario)
        if not usuario:
            return None, "Usuario no encontrado"

        # 2. Bloquear y obtener sesión presencial
        sesion_presencial_stmt = (
            select(SesionPresencial)
            .where(SesionPresencial.id_sesion == id_sesion)
            .with_for_update()
        )
        sesion_presencial = db.exec(sesion_presencial_stmt).first()

        if not sesion_presencial:
            return None, "Detalles de la sesión presencial no encontrados"

        # 3. Obtener datos relacionados de forma explícita
        sesion = db.get(Sesion, sesion_presencial.id_sesion)
        local = db.get(Local, sesion_presencial.id_local)
        
        if not sesion or not local:
             return None, "No se encontraron los detalles de la sesión o el local"
        
        servicio = db.get(Servicio, sesion.id_servicio)
        if not servicio:
            return None, "No se encontró el servicio asociado"

        # 4. Verificar reserva existente
        if existe_reserva_para_usuario(db, id_sesion, id_usuario):
            return None, "Ya existe una reserva para esta sesión"

        # 5. Chequear topes del plan
        comunidad_link = db.exec(
            select(ComunidadXServicio).where(ComunidadXServicio.id_servicio == servicio.id_servicio)
        ).first()
        if not comunidad_link:
            return None, "No se encontró la comunidad para este servicio"
        id_comunidad = comunidad_link.id_comunidad
        
        topes_disponibles_actual = None
        topes_consumidos_actual = None
        try:
            inscripcion = obtener_inscripcion_activa(db, cliente.id_cliente, id_comunidad)
            if es_plan_con_topes(db, inscripcion.id_inscripcion):
                detalle = db.exec(select(DetalleInscripcion).where(DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion).with_for_update()).first()
                if not detalle or detalle.topes_consumidos >= detalle.topes_disponibles:
                    return None, "No tienes suficientes créditos para reservar esta sesión."
                detalle.topes_consumidos += 1
                db.add(detalle)
                topes_disponibles_actual = detalle.topes_disponibles
                topes_consumidos_actual = detalle.topes_consumidos
        except Exception as e:
            return None, str(e)

        # 6. Verificar vacantes
        total_confirmadas = db.exec(
            select(func.count(Reserva.id_reserva))
            .where(Reserva.id_sesion == id_sesion, Reserva.estado_reserva == "confirmada")
        ).one()
        if total_confirmadas >= sesion_presencial.capacidad:
            return None, "No hay vacantes disponibles"

        # 7. Crear la reserva
        nueva_reserva = Reserva(
            id_sesion=id_sesion,
            id_cliente=cliente.id_cliente,
            estado_reserva="confirmada",
            fecha_creacion=datetime.utcnow()
        )
        db.add(nueva_reserva)
        db.flush() 

        # 8. Preparar y devolver detalles
        response_details = {
            "id_reserva": nueva_reserva.id_reserva,
            "nombre_servicio": servicio.nombre,
            "fecha": sesion.inicio.date(),
            "hora_inicio": sesion.inicio.time(),
            "hora_fin": sesion.fin.time(),
            "ubicacion": local.nombre,
            "direccion_detallada": local.direccion_detallada,
            "nombre_cliente": usuario.nombre,
            "apellido_cliente": usuario.apellido,
            "topes_disponibles": topes_disponibles_actual,
            "topes_consumidos": topes_consumidos_actual,
        }

        # 9. Enviar email en segundo plano
        bg_tasks.add_task(send_reservation_email, to_email=usuario.email, details=response_details)
        
        db.commit()

    return response_details, None

def obtener_resumen_sesion_presencial(db: Session, id_sesion: int):
    # CORRECTED QUERY: Uses Local.responsable instead of Profesional
    stmt = (
        select(
            Servicio.nombre,
            Sesion.inicio,
            Sesion.fin,
            Local.nombre,
            Local.direccion,
            Local.responsable, # Correct field
            Sesion.vacantes
        )
        .select_from(Sesion)
        .join(SesionPresencial, Sesion.id_sesion == SesionPresencial.id_sesion)
        .join(Local, SesionPresencial.id_local == Local.id_local)
        .join(Servicio, Sesion.id_servicio == Servicio.id_servicio)
        .where(Sesion.id_sesion == id_sesion)
    )
    
    result = db.exec(stmt).first()
    
    if not result:
        return None, "Sesión no encontrada"

    (
        nombre_servicio,
        inicio,
        fin,
        nombre_local,
        direccion_local,
        nombre_responsable, # Correctly unpacks responsable
        vacantes_disponibles
    ) = result
    
    summary = {
        "nombre_servicio": nombre_servicio,
        "fecha": inicio.strftime("%Y-%m-%d"),
        "hora_inicio": inicio.strftime("%H:%M"),
        "hora_fin": fin.strftime("%H:%M"),
        "ubicacion": nombre_local,
        "direccion": direccion_local,
        "responsable": nombre_responsable,
        "vacantes_disponibles": vacantes_disponibles,
    }
    
    return summary, None
