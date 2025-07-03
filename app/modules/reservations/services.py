from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
import pytz
import pandas as pd
import numpy as np
from fastapi import BackgroundTasks, HTTPException, UploadFile

from app.modules.billing.models import DetalleInscripcion
from app.modules.billing.services import (
    obtener_inscripcion_activa, 
    es_plan_con_topes
)
from app.modules.reservations.models import Reserva, Sesion, SesionPresencial, SesionVirtual
from app.modules.reservations.schemas import FormularioInfoResponse
from app.modules.services.models import ComunidadXServicio, Local, Profesional, Servicio
from app.modules.users.models import Cliente, Usuario
from utils.datetime_utils import convert_local_to_utc, convert_utc_to_local
from utils.email_brevo import send_form_email, send_reservation_email

from app.modules.reservations.schemas import SesionCargaMasiva
from pydantic import ValidationError

from datetime import datetime, timezone
from io import BytesIO


from app.modules.billing.models import Inscripcion, Plan
from typing import Tuple, Optional


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
        .where(ComunidadXServicio.estado == 1)
        .where(func.date(Sesion.inicio) >= fecha)
        .where(func.date(Sesion.inicio) < end_date)
        .where(Reserva.estado_reserva.in_(['confirmada', 'formulario_pendiente']))
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
        return []

    # 2) Convertir la fecha local a un rango UTC para la consulta
    start_of_day_local = datetime.combine(fecha_seleccionada, time.min)
    end_of_day_local = datetime.combine(fecha_seleccionada, time.max)
    
    start_of_day_utc = convert_local_to_utc(start_of_day_local)
    end_of_day_utc = convert_local_to_utc(end_of_day_local)

    if not start_of_day_utc or not end_of_day_utc:
        return [] # No se pudo convertir la zona horaria

    # 3) Armar la consulta para extraer la HORA de inicio de Sesion para esa fecha
    stmt = (
        select(Sesion.inicio) # Pedimos el datetime completo
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
            Sesion.inicio >= start_of_day_utc, # Filtro por rango UTC
            Sesion.inicio <= end_of_day_utc,
            SesionPresencial.id_local == id_local,
            Local.id_distrito == id_distrito,
        )
        .distinct()
    )

    raw_results = session.exec(stmt).all()
    
    # 4) Convertir los datetimes UTC a horas locales y formatear
    horas_locales: List[str] = []
    for dt_utc in raw_results:
        # raw_results ahora es una lista de datetimes
        local_dt = convert_utc_to_local(dt_utc)
        if local_dt:
            horas_locales.append(local_dt.strftime("%H:%M"))

    horas_locales.sort()

    return horas_locales

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
    try:
        hora_dt_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    except ValueError:
        # Si la hora no es válida, no habrá sesiones.
        return []
        
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
            Local.responsable.label("responsable"),
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
            Reserva.estado_reserva == "confirmada"
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
    sesion_actual: Sesion,
    id_comunidad: int
) -> None:
    """
    Verifica que el cliente no tenga otra reserva confirmada o pendiente
    que se cruce en el tiempo con la sesión actual, DENTRO DE LA MISMA COMUNIDAD.
    """
    inicio_nueva = sesion_actual.inicio
    fin_nueva = sesion_actual.fin

    # Query para buscar reservas que se solapen en el tiempo PARA LA MISMA COMUNIDAD
    reservas_en_conflicto = session.exec(
        select(Reserva)
        .join(Sesion, Reserva.id_sesion == Sesion.id_sesion)
        .where(
            Reserva.id_cliente == cliente_id,
            Reserva.id_comunidad == id_comunidad,  # <-- ¡Clave! Solo en la misma comunidad
            Reserva.estado_reserva.in_(["confirmada", "formulario_pendiente"]),
            inicio_nueva < Sesion.fin,
            fin_nueva > Sesion.inicio
        )
    ).all()

    if reservas_en_conflicto:
        raise HTTPException(
            status_code=409,
            detail="Ya tienes otra sesión activa que se cruza con ese horario en esta comunidad."
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
        estado_reserva="confirmada"
    )
    session.add(nueva)
    session.flush()  # asegura que nueva.id_reserva esté poblado
    return nueva

def crear_sesion_con_tipo(
    session: Session,
    id_servicio: int,
    tipo: str,
    descripcion: str,
    inicio: datetime,
    fin: datetime,
    id_profesional: Optional[int] = None,
    url_archivo: Optional[str] = None
) -> Sesion:
    """
    Crea una Sesion y, si es de tipo 'Virtual', crea también su SesionVirtual asociada.
    """
    sesion_obj = Sesion(
        id_servicio=id_servicio,
        tipo=tipo,
        descripcion=descripcion,
        inicio=inicio,
        fin=fin,
        fecha_creacion=datetime.now(timezone.utc),
        estado=True
    )

    session.add(sesion_obj)
    session.flush()  # Flush to get sesion_obj.id_sesion

    if tipo == "Virtual":
        if not id_profesional:
            raise ValueError("Se requiere un id_profesional para sesiones virtuales.")

        sesion_virtual_obj = SesionVirtual(
            id_sesion=sesion_obj.id_sesion,
            id_profesional=id_profesional,
            url_archivo=url_archivo
        )
        session.add(sesion_virtual_obj)
        session.flush()

    session.commit() # Commit the session and sesion_virtual (if created)
    session.refresh(sesion_obj)
    return sesion_obj

def obtener_url_archivo_virtual(session: Session, id_sesion: int) -> str | None:
    """
    Retorna la URL de archivo asociada a una sesión virtual, si existe.
    """
    sv = session.exec(
        select(SesionVirtual).where(SesionVirtual.id_sesion == id_sesion)
    ).first()
    return sv.url_archivo if sv else None


def crear_reserva_virtual_con_validaciones(
    session: Session,
    id_sesion: int,
    cliente_id: int,
    usuario_id: int,
    id_comunidad: int
) -> Reserva:
    # aquí abrimos la transacción exterior
    with session.begin():
        # bloque para el SAVEPOINT
        with session.begin_nested():
            sesion = obtener_sesion_bloqueada(session, id_sesion)
            validar_unicidad_virtual(session, sesion)
            validar_cliente_sin_conflicto(session, cliente_id, sesion, id_comunidad)

            inscripcion = obtener_inscripcion_activa(session, cliente_id, id_comunidad)
            plan = session.exec(
                select(Plan).where(Plan.id_plan == inscripcion.id_plan)
            ).one_or_none()
            if not plan:
                raise HTTPException(500, "El plan asociado a la inscripción no existe.")

            detalle = None
            if es_plan_con_topes(plan):
                detalle = obtener_detalle_topes_bloqueado(session, inscripcion.id_inscripcion)
                validar_topes_disponibles(detalle)

        # fuera del SAVEPOINT, pero dentro de la transacción padre:
        reserva = crear_reserva(
            session=session,
            sesion=sesion,
            cliente_id=cliente_id,
            comunidad_id=id_comunidad,
            usuario_id=usuario_id
        )

        if detalle:
            # descontamos los topes en la entidad
            detalle.topes_disponibles  -= 1
            detalle.topes_consumidos   += 1
            session.add(detalle)         # asegurar que SQLModel lo rastrea
            session.flush()             # enviar UPDATE al motor

        # al salir del `with session.begin():` se ejecuta el COMMIT
        return reserva

def obtener_sesion_bloqueada(session: Session, id_sesion: int) -> Sesion:
    sesion = session.exec(
        select(Sesion).where(Sesion.id_sesion == id_sesion).with_for_update()
    ).one_or_none()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return sesion


def validar_unicidad_virtual(session: Session, sesion: Sesion):
    if sesion.tipo == "Virtual":
        existe = session.exec(
            select(Reserva)
            .where(
                Reserva.id_sesion == sesion.id_sesion,
                Reserva.estado_reserva.in_(["confirmada", "formulario_pendiente"])
            ).with_for_update()
        ).first()
        if existe:
            raise HTTPException(
                status_code=409,
                detail="Ya existe una reserva activa para esta sesión virtual."
            )


def obtener_inscripcion_activa(session: Session, cliente_id: int, comunidad_id: int) -> Inscripcion:
    inscripcion = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == cliente_id,
            Inscripcion.id_comunidad == comunidad_id,
            Inscripcion.estado == 1
        )
    ).one_or_none()
    if not inscripcion:
        raise HTTPException(
            status_code=403,
            detail="No tienes una inscripción activa en esta comunidad."
        )
    return inscripcion


def es_plan_con_topes(plan: Plan) -> bool:
    return getattr(plan, "tiene_topes", False) or getattr(plan, "topes_maximos", None) is not None


def obtener_detalle_topes_bloqueado(session: Session, id_inscripcion: int) -> DetalleInscripcion:
    detalle = session.exec(
        select(DetalleInscripcion)
        .where(DetalleInscripcion.id_inscripcion == id_inscripcion)
        .with_for_update()
    ).one_or_none()
    if not detalle:
        raise HTTPException(
            status_code=500,
            detail="No se encontró el detalle de inscripción para topes."
        )
    return detalle


def validar_topes_disponibles(detalle: DetalleInscripcion):
    if detalle.topes_disponibles <= 0:
        raise HTTPException(
            status_code=409,
            detail="No tienes topes disponibles para realizar esta reserva."
        )


def descontar_topes(detalle: DetalleInscripcion):
    detalle.topes_disponibles -= 1
    detalle.topes_consumidos += 1


def crear_reserva(
    session: Session,
    sesion: Sesion,
    cliente_id: int,
    comunidad_id: int,
    usuario_id: int
) -> Reserva:
    reserva = Reserva(
        id_sesion       = sesion.id_sesion,
        id_cliente      = cliente_id,
        id_comunidad    = comunidad_id,
        estado_reserva  = "formulario_pendiente",
        fecha_reservada = sesion.inicio,
        creado_por      = str(usuario_id),
        fecha_creacion  = datetime.now(timezone.utc)
    )
    session.add(reserva)
    session.flush()
    return reserva



    
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

        # 4. VERIFICAR CRUCE DE HORARIOS EN LA MISMA COMUNIDAD
        comunidad_link = db.exec(
            select(ComunidadXServicio).where(
                ComunidadXServicio.id_servicio == servicio.id_servicio,
                ComunidadXServicio.estado == 1
            )
        ).first()
        if not comunidad_link:
            return None, "El servicio no está asociado a ninguna comunidad."
        id_comunidad = comunidad_link.id_comunidad

        try:
            validar_cliente_sin_conflicto(db, cliente.id_cliente, sesion, id_comunidad)
        except HTTPException as e:
            return None, e.detail

        # 5. Chequear topes del plan
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
    """
    Obtiene los detalles de una reserva específica para la pantalla de detalle,
    diferenciando entre sesiones presenciales y virtuales.
    """
    # 1. Validar que la reserva existe y pertenece al usuario
    cliente = db.exec(select(Cliente).where(Cliente.id_usuario == id_usuario)).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    reserva = db.get(Reserva, id_reserva)
    if not reserva or reserva.id_cliente != cliente.id_cliente:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no pertenece al usuario.")

    # 2. Cargar la sesión y el servicio asociados
    sesion = db.get(Sesion, reserva.id_sesion)
    if not sesion:
        raise HTTPException(status_code=404, detail="La sesión para esta reserva ya no existe.")
    
    servicio = db.get(Servicio, sesion.id_servicio)
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio para esta reserva ya no existe.")

    # 3. Preparar la respuesta base
    local_inicio = convert_utc_to_local(sesion.inicio)
    local_fin = convert_utc_to_local(sesion.fin)
    
    # 4. Calcular si la reserva ya pasó comparando con la fecha/hora actual de Lima
    ahora_lima = datetime.now(pytz.timezone("America/Lima"))
    reserva_pasada = False
    if local_fin:
        # La reserva se considera pasada si la hora de fin ya pasó
        local_fin_dt = datetime.combine(local_inicio.date(), local_fin.time()) if local_inicio else None
        if local_fin_dt:
            local_fin_dt = pytz.timezone("America/Lima").localize(local_fin_dt)
            reserva_pasada = local_fin_dt < ahora_lima
    
    response_data = {
        "id_reserva": id_reserva,
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
        "estado_reserva": reserva.estado_reserva,
        "reserva_pasada": reserva_pasada
    }

    # 4. Obtener detalles específicos según el tipo de sesión
    if sesion.tipo == "Presencial":
        sesion_presencial = db.exec(select(SesionPresencial).where(SesionPresencial.id_sesion == sesion.id_sesion)).first()
        if sesion_presencial:
            local = db.get(Local, sesion_presencial.id_local)
            if local:
                response_data["responsable"] = local.responsable
                response_data["nombre_local"] = local.nombre or "Nombre no disponible"
                response_data["direccion"] = local.direccion_detallada or "Dirección no especificada"

    elif sesion.tipo == "Virtual":
        sesion_virtual = db.exec(select(SesionVirtual).where(SesionVirtual.id_sesion == sesion.id_sesion)).first()
        if sesion_virtual:
            response_data["url_meeting"] = sesion_virtual.url_meeting or "Link no disponible"
            if sesion_virtual.id_profesional:
                profesional = db.get(Profesional, sesion_virtual.id_profesional)
                if profesional:
                    response_data["nombre_profesional"] = profesional.nombre_completo

    return response_data, None

def obtener_info_formulario(db: Session, id_sesion: int, cliente_id: int):
    # 1. Validar que la reserva existe y pertenece al cliente
    reserva = db.exec(
        select(Reserva).where(Reserva.id_sesion == id_sesion, Reserva.id_cliente == cliente_id)
    ).one_or_none()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no pertenece al cliente.")

    # 2. Obtener la sesión virtual y el profesional
    sesion_virtual = db.exec(
        select(SesionVirtual).where(SesionVirtual.id_sesion == id_sesion)
    ).one_or_none()
    if not sesion_virtual:
        raise HTTPException(status_code=404, detail="Sesión virtual no encontrada.")
        
    profesional = db.get(Profesional, sesion_virtual.id_profesional)
    if not profesional:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")

    # 3. Construir la respuesta
    return {
        "profesional_nombre": profesional.nombre_completo,
        "fecha_sesion": sesion_virtual.sesion.inicio.date(),
        "hora_inicio": sesion_virtual.sesion.inicio.time(),
        "hora_fin": sesion_virtual.sesion.fin.time(),
        "url_formulario": sesion_virtual.url_archivo,
        "formulario_completado": reserva.archivo is not None
    }

async def completar_formulario_virtual(
    session: Session, 
    id_sesion: int, 
    cliente_id: int, 
    file: UploadFile,
    bg_tasks: BackgroundTasks,
    profesional_email: str,
    profesional_nombre: str,
    cliente_nombre: str
):
    """
    Guarda el archivo del formulario en la reserva y envía un correo al profesional.
    """
    reserva = session.exec(
        select(Reserva).where(Reserva.id_sesion == id_sesion, Reserva.id_cliente == cliente_id)
    ).one_or_none()

    if not reserva:
        raise HTTPException(status_code=404, detail="No se encontró una reserva para el usuario en esta sesión.")
    
    if reserva.archivo is not None:
        raise HTTPException(status_code=400, detail="El formulario para esta reserva ya ha sido enviado.")

    # Obtenemos la sesión para los detalles del correo
    sesion_obj = session.get(Sesion, id_sesion)
    if not sesion_obj:
         raise HTTPException(status_code=404, detail="No se encontró la sesión.")

    # Actualizamos la reserva
    file_content = await file.read()
    reserva.archivo = file_content
    reserva.estado_reserva = "confirmada" # Cambiamos el estado
    session.add(reserva)
    session.commit()
    
    # Preparamos los detalles para el correo
    email_details = {
        "nombre_profesional": profesional_nombre,
        "nombre_cliente": cliente_nombre,
        "fecha_sesion": sesion_obj.inicio.strftime("%d/%m/%Y"),
        "hora_inicio": sesion_obj.inicio.strftime("%H:%M"),
    }

    # Enviamos el correo en segundo plano
    bg_tasks.add_task(
        send_form_email,
        to_email=profesional_email,
        file_content=file_content,
        filename=file.filename,
        details=email_details
    )

    return {"mensaje": "Archivo enviado al profesional correspondiente."}

def cancelar_reserva_por_id(db: Session, id_reserva: int, id_usuario: int):
    """
    Cancela una reserva cambiando su estado a 'cancelada'.
    No devuelve el cupo/crédito al usuario.
    """
    # 1. Buscar al cliente
    cliente = db.exec(select(Cliente).where(Cliente.id_usuario == id_usuario)).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    # 2. Buscar la reserva y validar que pertenece al cliente
    reserva = db.get(Reserva, id_reserva)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    
    if reserva.id_cliente != cliente.id_cliente:
        raise HTTPException(status_code=403, detail="No tienes permiso para cancelar esta reserva.")

    # 3. Validar que la reserva está en un estado cancelable
    if reserva.estado_reserva != "confirmada":
        raise HTTPException(
            status_code=400,
            detail=f"La reserva ya está en estado '{reserva.estado_reserva}' y no puede ser cancelada."
        )

    # 4. Cambiar el estado y guardar en la base de datos
    reserva.estado_reserva = "cancelada"
    reserva.modificado_por = str(id_usuario)
    reserva.fecha_modificacion = datetime.utcnow()
    
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    
    return {"message": "Reserva cancelada exitosamente."}

def verificar_cruce_de_reservas(db: Session, id_cliente: int, id_comunidad: int, inicio_nueva: datetime, fin_nueva: datetime) -> bool:
    """
    Verifica si un cliente ya tiene una reserva confirmada en una comunidad
    que se cruce en tiempo con una nueva sesión.
    """
    reservas_existentes = db.exec(
        select(Reserva)
        .join(Sesion, Reserva.id_sesion == Sesion.id_sesion)
        .join(Servicio, Sesion.id_servicio == Servicio.id_servicio)
        .join(ComunidadXServicio, Servicio.id_servicio == ComunidadXServicio.id_servicio)
        .where(
            Reserva.id_cliente == id_cliente,
            ComunidadXServicio.id_comunidad == id_comunidad,
            ComunidadXServicio.estado == 1,
            Reserva.estado_reserva == "confirmada",
            Sesion.inicio < fin_nueva,
            Sesion.fin > inicio_nueva
        )
    ).first()

    return reservas_existentes is not None



def procesar_archivo_sesiones_virtuales(db: Session, archivo, creado_por: str):
    df = pd.read_excel(BytesIO(archivo.file.read()), engine="openpyxl")
    df = df.replace({np.nan: None})

    resumen = {
        "insertados": 0,
        "errores": []
    }

    for idx, fila in df.iterrows():
        try:
            datos = SesionCargaMasiva.model_validate(fila.to_dict())
            procesar_fila_sesion_virtual(datos, db, creado_por)
            resumen["insertados"] += 1
        except ValidationError as ve:
            resumen["errores"].append(f"Fila {idx + 2}: Error de validación - {ve}")
        except Exception as e:
            db.rollback()
            resumen["errores"].append(f"Fila {idx + 2}: {str(e)}")

    return resumen


def procesar_fila_sesion_virtual(datos: SesionCargaMasiva, db: Session, creado_por: str):
    ahora = datetime.now(timezone.utc)

    # ✅ Normalizar fechas para evitar errores de comparación
    if datos.fecha_inicio.tzinfo is None:
        datos.fecha_inicio = datos.fecha_inicio.replace(tzinfo=timezone.utc)
    if datos.fecha_fin.tzinfo is None:
        datos.fecha_fin = datos.fecha_fin.replace(tzinfo=timezone.utc)
        
    if datos.fecha_inicio < ahora:
        raise ValueError(
            f"No se puede crear una sesión en el pasado: {datos.fecha_inicio}"
        )

    if datos.fecha_inicio >= datos.fecha_fin:
        raise ValueError(
            f"La fecha de inicio debe ser anterior a la fecha de fin."
        )

    # Validar servicio virtual
    servicio = db.exec(
        select(Servicio).where(Servicio.id_servicio == datos.id_servicio)
    ).first()
    if not servicio:
        raise ValueError(f"Servicio con ID {datos.id_servicio} no existe.")
    if servicio.modalidad.lower() != "virtual":
        raise ValueError(f"El servicio {datos.id_servicio} no es de modalidad virtual.")

    # Validar profesional
    profesional = db.exec(
        select(Profesional).where(Profesional.id_profesional == datos.id_profesional)
    ).first()
    if not profesional:
        raise ValueError(f"Profesional con ID {datos.id_profesional} no existe.")

    # Validaciones de conflicto lógico
    validar_sesion_duplicada(db, datos)
    validar_sesion_solapada(db, datos)

    # Si todo está bien, ahora sí se crea la sesión
    nueva_sesion = Sesion(
        id_servicio=datos.id_servicio,
        tipo="Virtual",
        descripcion=datos.descripcion or f"Sesión virtual de servicio {datos.id_servicio}",
        inicio=datos.fecha_inicio,
        fin=datos.fecha_fin,
        creado_por=creado_por,
        fecha_creacion=datetime.now(timezone.utc),
        estado=1
    )
    db.add(nueva_sesion)
    db.flush()  # Ahora sí, porque ya validamos todo

    nueva_virtual = SesionVirtual(
        id_sesion=nueva_sesion.id_sesion,
        id_profesional=datos.id_profesional,
        url_meeting=datos.url_meeting,
        url_archivo=datos.url_archivo,
        creado_por=creado_por,
        fecha_creacion=datetime.now(timezone.utc),
        estado=1
    )
    db.add(nueva_virtual)
    db.commit()


def validar_sesion_duplicada(db: Session, datos: SesionCargaMasiva):
    existe = db.exec(
        select(Sesion)
        .join(SesionVirtual, Sesion.id_sesion == SesionVirtual.id_sesion)
        .where(
            Sesion.id_servicio == datos.id_servicio,
            Sesion.inicio == datos.fecha_inicio,
            SesionVirtual.id_profesional == datos.id_profesional
        )
    ).first()

    if existe:
        raise ValueError(
            f"Ya existe una sesión virtual programada para el servicio {datos.id_servicio}, "
            f"con el profesional {datos.id_profesional} exactamente a las {datos.fecha_inicio}."
        )


def validar_sesion_solapada(db: Session, datos: SesionCargaMasiva):
    solapada = db.exec(
        select(Sesion)
        .join(SesionVirtual, Sesion.id_sesion == SesionVirtual.id_sesion)
        .where(
            SesionVirtual.id_profesional == datos.id_profesional,
            Sesion.id_servicio == datos.id_servicio,
            Sesion.inicio < datos.fecha_fin,
            Sesion.fin > datos.fecha_inicio
        )
    ).first()

    if solapada:
        raise ValueError(
            f"El profesional {datos.id_profesional} ya tiene una sesión que se cruza entre "
            f"{datos.fecha_inicio} y {datos.fecha_fin} para el mismo servicio {datos.id_servicio}."
        )




def obtener_resumen_reserva_virtual(
    db: Session, id_reserva: int, id_usuario: int
) -> Tuple[Optional[dict], Optional[str]]:
    # 1. Buscar la reserva
    reserva = db.get(Reserva, id_reserva)
    if not reserva:
        return None, "Reserva no encontrada"
    
    # 2. Verificar que le pertenece al usuario
    cliente = db.get(Cliente, reserva.id_cliente)
    if not cliente or cliente.id_usuario != id_usuario:
        return None, "No autorizado para ver esta reserva"

    # 3. Obtener los datos del usuario (nombre y apellido)
    usuario = db.get(Usuario, cliente.id_usuario)
    if not usuario:
        return None, "No se encontró el usuario asociado"

    # 4. Obtener datos de la sesión y recurso virtual
    stmt = (
        select(
            Servicio.nombre,
            Sesion.inicio,
            Sesion.fin,
            SesionVirtual.url_archivo
        )
        .join(Servicio, Sesion.id_servicio == Servicio.id_servicio)
        .join(SesionVirtual, Sesion.id_sesion == SesionVirtual.id_sesion)
        .where(Sesion.id_sesion == reserva.id_sesion)
    )
    result = db.exec(stmt).first()

    if not result:
        return None, "Sesión virtual no encontrada"

    nombre_servicio, inicio, fin, url_archivo = result

    local_inicio = convert_utc_to_local(inicio)
    local_fin = convert_utc_to_local(fin)

    resumen = {
        "id_sesion": reserva.id_sesion,
        "fecha": local_inicio.date(),
        "hora_inicio": local_inicio.strftime("%H:%M"),
        "hora_fin": local_fin.strftime("%H:%M"),
        "link_formulario": url_archivo or "",
        "nombres": usuario.nombre,
        "apellidos": usuario.apellido,
        "mensaje_exito": "Reserva realizada con éxito.",
        "nota": (
            "Puede llenar este link más tarde desde la sección 'mis reservas', "
            "pero debe completarlo para que el profesional pueda atenderlo."
        )
    }

    return resumen, None
