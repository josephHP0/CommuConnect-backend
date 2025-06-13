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
from utils.datetime_utils import convert_utc_to_local, convert_local_to_utc

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
    
    # --- INICIO DEL CAMBIO ---
    horas_iso: List[str] = []
    for t in raw_results:
        # raw_results puede ser una tupla (time,)
        time_obj = t[0] if isinstance(t, tuple) else t
        
        # Creamos un datetime 'dummy' con la fecha de hoy para poder convertirlo
        # ya que la función de conversión espera un datetime, no solo un time.
        dummy_datetime_utc = datetime.combine(date.today(), time_obj)
        local_dt = convert_utc_to_local(dummy_datetime_utc)
        
        if local_dt:
            horas_iso.append(local_dt.strftime("%H:%M:%S"))
    # --- FIN DEL CAMBIO ---

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

    # --- INICIO DEL CAMBIO ---
    # 2) Combinar fecha y hora local, y convertir a UTC
    hora_dt_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    local_dt = datetime.combine(fecha_seleccionada, hora_dt_obj)
    utc_dt = convert_local_to_utc(local_dt)

    if not utc_dt:
        # Esto no debería pasar si la fecha y hora son válidas, pero es una buena práctica
        return []

    # Extraemos la fecha y hora UTC para la consulta
    fecha_utc = utc_dt.date()
    hora_utc_str = utc_dt.strftime("%H:%M:%S")
    # --- FIN DEL CAMBIO ---

    # 3) Hacer la consulta filtrando con los valores UTC
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
            func.date(Sesion.inicio)== fecha_utc, # Usar fecha UTC
            func.time(Sesion.inicio)== hora_utc_str,    # Usar hora UTC
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
        # --- INICIO DEL CAMBIO ---
        local_inicio = convert_utc_to_local(dt_inicio)
        local_fin = convert_utc_to_local(dt_fin)
        # --- FIN DEL CAMBIO ---

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
            "fecha":               local_inicio.date() if local_inicio else fecha_sesion,
            "ubicacion":           ubicacion,
            "responsable":         responsable,
            "hora_inicio":         local_inicio.strftime("%H:%M") if local_inicio else "N/A",
            "hora_fin":            local_fin.strftime("%H:%M") if local_fin else "N/A",
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

    fechas_formateadas = []
    for sv in resultados:
        if sv.sesion and sv.sesion.inicio:
            # --- INICIO DEL CAMBIO ---
            local_inicio = convert_utc_to_local(sv.sesion.inicio)
            # --- FIN DEL CAMBIO ---
            fechas_formateadas.append({
                "id_sesion_virtual": sv.id_sesion_virtual,
                "id_sesion": sv.sesion.id_sesion,
                "dia": local_inicio.strftime("%Y-%m-%d") if local_inicio else None,
                "hora": local_inicio.strftime("%H:%M:%S") if local_inicio else None
            })
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

    # --- INICIO DEL CAMBIO ---
    local_inicio = convert_utc_to_local(dt_inicio)
    local_fin = convert_utc_to_local(dt_fin)
    # --- FIN DEL CAMBIO ---

    resumen = {
        "id_sesion": id_ses,
        "id_sesion_presencial": id_ses_pres,
        "fecha": local_inicio.date() if local_inicio else fecha_sesion,
        "ubicacion": ubicacion,
        "responsable": responsable,
        "hora_inicio": local_inicio.strftime("%H:%M") if local_inicio else "N/A",
        "hora_fin": local_fin.strftime("%H:%M") if local_fin else "N/A",
        "vacantes_totales": vac_tot,
        "nombres": usuario.nombre,
        "apellidos": usuario.apellido
    }
    
    return resumen, None

def crear_reserva_presencial(db: Session, id_sesion: int, id_usuario: int, bg_tasks: BackgroundTasks):
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

        # --- INICIO DEL CAMBIO ---
        local_inicio = convert_utc_to_local(sesion.inicio)
        local_fin = convert_utc_to_local(sesion.fin)
        # --- FIN DEL CAMBIO ---

        # 8. Preparar y devolver detalles
        response_details = {
            "id_reserva": nueva_reserva.id_reserva,
            "nombre_servicio": servicio.nombre,
            "fecha": local_inicio.date() if local_inicio else None,
            "hora_inicio": local_inicio.time() if local_inicio else None,
            "hora_fin": local_fin.time() if local_fin else None,
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
        "fecha": inicio.strftime("%d/%m/%Y"),
        "hora_inicio": inicio.strftime("%H:%M"),
        "hora_fin": fin.strftime("%H:%M"),
        "ubicacion": nombre_local,
        "direccion": direccion_local,
        "responsable": nombre_responsable,
        "vacantes_disponibles": vacantes_disponibles,
    }
    
    return summary, None

def get_reservation_details(db: Session, id_reserva: int, id_usuario: int):
    # 1. Validar que la reserva existe y pertenece al usuario
    reserva = db.get(Reserva, id_reserva)
    cliente = db.exec(select(Cliente).where(Cliente.id_usuario == id_usuario)).first()

    if not reserva or not cliente or reserva.id_cliente != cliente.id_cliente:
        return None, "Reserva no encontrada o no pertenece al usuario."

    # 2. Obtener la sesión y el servicio
    sesion = db.get(Sesion, reserva.id_sesion)
    if not sesion:
        return None, "Sesión asociada no encontrada."
    
    servicio = db.get(Servicio, sesion.id_servicio)
    if not servicio:
        return None, "Servicio asociado no encontrado."

    # Convertir las horas a la zona horaria local
    local_inicio = convert_utc_to_local(sesion.inicio)
    local_fin = convert_utc_to_local(sesion.fin)

    formulario_completado = sesion.tipo == "Virtual" and reserva.archivo is not None

    response_data = {
        "nombre_servicio": servicio.nombre,
        "fecha": local_inicio.date() if local_inicio else None,
        "hora_inicio": local_inicio.time() if local_inicio else None,
        "hora_fin": local_fin.time() if local_fin else None,
        "tipo_sesion": sesion.tipo,
        "responsable": None,
        "nombre_local": None,
        "direccion": None,
        "url_meeting": None,
        "nombre_profesional": None,
        "formulario_completado": formulario_completado
    }

    # 3. Obtener detalles específicos según el tipo de sesión
    if sesion.tipo == "Presencial":
        sesion_presencial = db.exec(select(SesionPresencial).where(SesionPresencial.id_sesion == sesion.id_sesion)).first()
        if sesion_presencial:
            local = db.get(Local, sesion_presencial.id_local)
            if local:
                response_data["responsable"] = local.responsable
                response_data["nombre_local"] = local.nombre or "Nombre no disponible"
                response_data["direccion"] = local.direccion_detallada or "Dirección no especificada"

    elif sesion.tipo == "Virtual":
        from app.modules.services.models import Profesional
        sesion_virtual = db.exec(select(SesionVirtual).where(SesionVirtual.id_sesion == sesion.id_sesion)).first()
        if sesion_virtual:
            response_data["url_meeting"] = sesion_virtual.url_meeting or "Link no disponible"
            if sesion_virtual.id_profesional:
                profesional = db.get(Profesional, sesion_virtual.id_profesional)
                if profesional:
                    response_data["nombre_profesional"] = profesional.nombre_completo

    return response_data, None
