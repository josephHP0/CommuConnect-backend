from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy import text
from utils.datetime_utils import convert_utc_to_local

from app.modules.communities.models import ClienteXComunidad, Comunidad, ComunidadXPlan
from .schemas import ComunidadXPlanCreate, DetalleInscripcionCreate, PlanCreate, PlanUpdate
from datetime import datetime

from app.core.enums import MetodoPago
from .models import Inscripcion, Pago, Plan, DetalleInscripcion

from sqlalchemy import and_

def get_planes(session: Session):
    return session.exec(select(Plan)).all()

def crear_pago_pendiente(session: Session, id_plan: int, creado_por: str):
    plan = session.get(Plan, id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    pago = Pago(
        monto=plan.precio,
        fecha_pago=None,
        metodo_pago=None,
        creado_por=creado_por,
        estado=0
    )
    session.add(pago)
    session.commit()
    session.refresh(pago)
    return pago

def crear_inscripcion(
    session: Session,
    id_plan: Optional[int],
    id_comunidad: int,
    id_cliente: int,
    id_pago: Optional[int],
    creado_por: str
):
    from datetime import timedelta

    ahora = datetime.utcnow()
    hace_un_mes = ahora - timedelta(days=30)

    # Busca inscripción previa pendiente en el último mes (pendiente de plan o de pago)
    inscripcion_previa = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado.in_([2, 3]), # type: ignore
            Inscripcion.fecha_creacion >= hace_un_mes
        )
    ).first()

    # Busca inscripción previa ya pagada (activa)
    inscripcion_pagada = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 1
        )
    ).first()
    nuevo_estado = 0
    # Determina el nuevo estado según los datos recibidos
    if not id_plan and not id_pago:
        nuevo_estado = 2  # Pendiente de plan

    # --- AGREGADO: función para crear la relación si no existe ---
    def asegurar_relacion_clientexcomunidad():
        existe = session.exec(
            select(ClienteXComunidad).where(
                ClienteXComunidad.id_cliente == id_cliente,
                ClienteXComunidad.id_comunidad == id_comunidad
            )
        ).first()
        if not existe:
            relacion = ClienteXComunidad(
                id_cliente=id_cliente,
                id_comunidad=id_comunidad
            )
            session.add(relacion)
            session.commit()
    # ------------------------------------------------------------

    if inscripcion_previa:
        # Sobrescribe la inscripción pendiente
        inscripcion_previa.id_plan = id_plan
        inscripcion_previa.id_pago = id_pago
        inscripcion_previa.modificado_por = creado_por
        inscripcion_previa.fecha_modificacion = ahora
        inscripcion_previa.estado = 3
        session.add(inscripcion_previa)
        session.commit()
        session.refresh(inscripcion_previa)
        asegurar_relacion_clientexcomunidad()
        return inscripcion_previa
    elif inscripcion_pagada:
        # Crea nueva inscripción con el estado correspondiente
        inscripcion = Inscripcion(
            estado=nuevo_estado,
            id_plan=id_plan,
            id_comunidad=id_comunidad,
            id_cliente=id_cliente,
            id_pago=id_pago,
            creado_por=creado_por,
            fecha_creacion=ahora
        )
        session.add(inscripcion)
        session.commit()
        session.refresh(inscripcion)
        asegurar_relacion_clientexcomunidad()
        return inscripcion
    else:
        # No hay inscripción previa, crea nueva
        if not id_plan and not id_pago:
            nuevo_estado = 2  # Pendiente de plan
        elif id_pago:
            nuevo_estado = 3  # Pendiente de pago
        inscripcion = Inscripcion(
            estado=nuevo_estado,
            id_plan=id_plan,
            id_comunidad=id_comunidad,
            id_cliente=id_cliente,
            id_pago=id_pago,
            creado_por=creado_por,
            fecha_creacion=ahora
        )
        session.add(inscripcion)
        session.commit()
        session.refresh(inscripcion)
        asegurar_relacion_clientexcomunidad()
        return inscripcion

def pagar_pendiente(
    session: Session,
    id_cliente: int,
    id_comunidad: int,
    creado_por: str
):
    try:
        session.execute(
            text("CALL PagarPendiente(:p_id_cliente, :p_id_comunidad, :p_creado_por)"),
            {
                "p_id_cliente": id_cliente,
                "p_id_comunidad": id_comunidad,
                "p_creado_por": creado_por
            }
        )
        session.commit()
        return {"ok": True, "message": "Pago realizado exitosamente"}
    except Exception as e:
        session.rollback()
        detail = str(e)
        if hasattr(e, "orig") and hasattr(e.orig, "args") and len(e.orig.args) > 1: # type: ignore
            detail = e.orig.args[1] # type: ignore
        raise HTTPException(status_code=400, detail=detail)

def obtener_inscripcion_activa(session: Session, id_cliente: int, id_comunidad: int) -> Inscripcion:
    query = select(Inscripcion).where(
        and_(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 1  # Solo inscripciones activas
        )
    )
    inscripcion = session.exec(query).first()

    if not inscripcion:
        raise HTTPException(
            status_code=404,
            detail="El cliente no tiene inscripción activa en esta comunidad"
        )

    return inscripcion


def es_plan_con_topes(session: Session, id_inscripcion: int) -> bool:
    query = select(DetalleInscripcion).where(
        DetalleInscripcion.id_inscripcion == id_inscripcion
    )
    resultado = session.exec(query).first()

    return resultado is not None

def obtener_detalle_topes(session: Session, id_inscripcion: int) -> dict:
    detalle = session.exec(
        select(DetalleInscripcion).where(
            DetalleInscripcion.id_inscripcion == id_inscripcion
        )
    ).first()

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el detalle de topes para esta inscripción"
        )

    return {
        "topes_disponibles": detalle.topes_disponibles,
        "topes_consumidos": detalle.topes_consumidos
    }


def crear_detalle_inscripcion(
    session: Session,
    id_inscripcion: int,
    creado_por: str
) -> DetalleInscripcion:
    from datetime import timedelta

    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    plan = session.get(Plan, inscripcion.id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    fecha_inicio = datetime.utcnow()
    fecha_fin = fecha_inicio + timedelta(days=30)
    # Si el id_plan es impar, fecha_fin en 1 año; si es par, en 1 mes
    if plan.duracion == 12:
        fecha_fin = fecha_inicio + timedelta(days=365)
    elif plan.duracion == 1:
        fecha_fin = fecha_inicio + timedelta(days=30)

    detalle = DetalleInscripcion(
        id_inscripcion=id_inscripcion,
        fecha_registro=fecha_inicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        topes_disponibles=plan.topes, # type: ignore
        topes_consumidos=0,
        fecha_creacion=fecha_inicio,
        creado_por=creado_por,
        fecha_modificacion=None,
        modificado_por=None,
        estado=1
    )
    session.add(detalle)
    session.commit()
    session.refresh(detalle)
    return detalle


def tiene_membresia_asociada(
    session: Session,
    cliente_id: int
) -> bool:
    """
    Retorna True si el cliente tiene al menos una inscripción
    activa (estado = 1) en cualquier comunidad.
    """
    stmt = (
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == cliente_id,
            Inscripcion.estado == 1  # Solo activas
        )
    )
    return session.exec(stmt).first() is not None


def tiene_membresia_activa_en_comunidad(session: Session, cliente_id: int, id_comunidad: int) -> bool:
    inscripcion = session.exec(
        select(Inscripcion).where(
            Inscripcion.id_cliente == cliente_id,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 1  # Activa
        )
    ).first()

    return bool(inscripcion)


def tiene_topes_disponibles(session: Session, id_cliente: int, id_comunidad: int) -> bool:
    inscripcion = obtener_inscripcion_activa(session, id_cliente, id_comunidad)

    if not es_plan_con_topes(session, inscripcion.id_inscripcion): # type: ignore
        return True  # Plan ilimitado, puede reservar sin topes

    detalle = obtener_detalle_topes(session, inscripcion.id_inscripcion) # type: ignore
    return detalle["topes_disponibles"] > 0

def congelar_inscripcion(session: Session, id_inscripcion: int, modificado_por: str):
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    inscripcion.estado = 0  # Congelado
    inscripcion.modificado_por = modificado_por
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion

def reactivar_inscripcion(session: Session, id_inscripcion: int, modificado_por: str):
    inscripcion = session.get(Inscripcion, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    if inscripcion.estado != 0:
        raise HTTPException(status_code=400, detail="Solo se pueden reactivar inscripciones congeladas")
    inscripcion.estado = 1  # Activa
    inscripcion.modificado_por = modificado_por
    inscripcion.fecha_modificacion = datetime.utcnow()
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion

def obtener_planes_por_comunidad(db: Session, id_comunidad: int) -> list[Plan]:
    query = (
        select(Plan)
        .join(ComunidadXPlan, Plan.id_plan == ComunidadXPlan.id_plan) # type: ignore
        .where(ComunidadXPlan.id_comunidad == id_comunidad)
        .where(ComunidadXPlan.estado == 1)
        .where(Plan.estado == 1)
    )
    return db.exec(query).all() # type: ignore

def agregar_plan_a_comunidad_serv(
    db: Session,
    data: ComunidadXPlanCreate,
    creado_por: str
) -> ComunidadXPlan:

    # Validar si ya existe
    existe = db.exec(
        select(ComunidadXPlan).where(
            ComunidadXPlan.id_comunidad == data.id_comunidad,
            ComunidadXPlan.id_plan == data.id_plan
        )
    ).first()

    if existe:
        raise HTTPException(status_code=409, detail="El plan ya está asociado a esta comunidad.")

    nueva_relacion = ComunidadXPlan(
        id_comunidad=data.id_comunidad,
        id_plan=data.id_plan,
        fecha_creacion=datetime.utcnow(),
        creado_por=creado_por,
        estado=1
    )

    db.add(nueva_relacion)
    db.commit()
    db.refresh(nueva_relacion)
    return nueva_relacion

def obtener_planes_no_asociados(db: Session, id_comunidad: int) -> list[Plan]:
    # Subconsulta: obtener ids de planes ya asociados a la comunidad
    subquery = (
        select(ComunidadXPlan.id_plan)
        .where(ComunidadXPlan.id_comunidad == id_comunidad)
    )

    # Consulta principal: obtener planes cuyo id no está en la subconsulta
    query = (
        select(Plan)
        .where(Plan.id_plan.not_in(subquery)) # type: ignore
        .where(Plan.estado == 1)  # solo planes activos, opcional
    )

    return db.exec(query).all() # type: ignore

def crear_plan(session: Session, plan_data: PlanCreate, creado_por: str) -> Plan:
    plan = Plan(**plan_data.dict(), creado_por=creado_por, estado=1)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan

def eliminar_plan_logico(session: Session, id_plan: int, modificado_por: str) -> Plan:
    plan = session.get(Plan, id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    plan.estado = 0  # Inactivo
    plan.modificado_por = modificado_por
    plan.fecha_modificacion = datetime.utcnow()
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan

def actualizar_plan(session: Session, id_plan: int, plan_data: 'PlanUpdate', modificado_por: str) -> Plan:
    plan = session.get(Plan, id_plan)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    # Solo actualiza los campos que vienen en la petición
    for field, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, field, value)
    plan.modificado_por = modificado_por
    plan.fecha_modificacion = datetime.utcnow()
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan

def calcular_estado_suspension(suspension) -> Dict[str, Any]:
    """
    Calcula el estado visual de una suspensión EN TIEMPO REAL basándose en:
    - Estado de la base de datos
    - Fechas de inicio y fin
    - Fecha actual
    
    Returns:
        Dict con estado_visual, color, y acciones_disponibles
    """
    import pytz
    
    # 🔄 Usar zona horaria de Lima para comparaciones consistentes
    lima_tz = pytz.timezone("America/Lima")
    ahora = datetime.now(lima_tz).replace(tzinfo=None)  # Convertir a naive datetime para comparar
    
    estado_bd = suspension.estado
    fecha_inicio = suspension.fecha_inicio
    fecha_fin = suspension.fecha_fin
    
    # Estados para solicitudes PENDIENTES (estado_bd == 2)
    if estado_bd == 2:  # Pendiente - aquí importa la fecha_inicio
        if not fecha_inicio:
            return {
                "estado_visual": "Pendiente",
                "color": "warning",
                "acciones_disponibles": ["ver", "aprobar", "rechazar"],
                "puede_modificar": True
            }
        
        # Calcular días hasta el inicio de la suspensión
        dias_hasta_inicio = (fecha_inicio - ahora).days
        
        # La fecha de inicio ya pasó - admin no decidió a tiempo
        if ahora > fecha_inicio:
            return {
                "estado_visual": "Vencida",
                "color": "danger",
                "acciones_disponibles": ["ver"],
                "puede_modificar": False,
                "mensaje": "La fecha de inicio ya pasó sin decisión del admin"
            }
        
        # Faltan 7 días o menos para el inicio - URGENTE
        elif dias_hasta_inicio <= 7:
            return {
                "estado_visual": "Por vencer",
                "color": "warning",
                "acciones_disponibles": ["ver", "aprobar", "rechazar"],
                "puede_modificar": True,
                "dias_hasta_inicio": dias_hasta_inicio,
                "mensaje": f"Debe decidir en {dias_hasta_inicio} días"
            }
        
        # Tiempo suficiente para decidir
        else:
            return {
                "estado_visual": "Pendiente",
                "color": "info",
                "acciones_disponibles": ["ver", "aprobar", "rechazar"],
                "puede_modificar": True,
                "dias_hasta_inicio": dias_hasta_inicio
            }
    
    # Estados para solicitudes RECHAZADAS (estado_bd == 0)
    elif estado_bd == 0:  # Rechazada
        return {
            "estado_visual": "Rechazada", 
            "color": "danger",
            "acciones_disponibles": ["ver"],
            "puede_modificar": False
        }
    
    # Estados para solicitudes ACEPTADAS (estado_bd == 1)
    elif estado_bd == 1:  # Aceptada - calcular basándose en fechas de la suspensión activa
        if not fecha_inicio or not fecha_fin:
            return {
                "estado_visual": "Aceptada",
                "color": "success",
                "acciones_disponibles": ["ver"],
                "puede_modificar": False
            }
        
        # Calcular días hasta el fin de la suspensión
        dias_hasta_fin = (fecha_fin - ahora).days
        
        # Suspensión aún no ha comenzado (programada para el futuro)
        if ahora < fecha_inicio:
            dias_hasta_inicio = (fecha_inicio - ahora).days
            return {
                "estado_visual": "Programada",
                "color": "info",
                "acciones_disponibles": ["ver"],
                "puede_modificar": False,
                "dias_hasta_inicio": dias_hasta_inicio,
                "mensaje": f"Comenzará en {dias_hasta_inicio} días"
            }
        
        # Suspensión ya terminó
        elif ahora > fecha_fin:
            return {
                "estado_visual": "Completada",
                "color": "secondary",
                "acciones_disponibles": ["ver"],
                "puede_modificar": False,
                "mensaje": "La suspensión ya terminó"
            }
        
        # Suspensión está por terminar (7 días o menos)
        elif dias_hasta_fin <= 7:
            return {
                "estado_visual": "Por terminar",
                "color": "warning",
                "acciones_disponibles": ["ver"],
                "puede_modificar": False,
                "dias_restantes": dias_hasta_fin,
                "mensaje": f"Termina en {dias_hasta_fin} días"
            }
        
        # Suspensión activa normal
        else:
            return {
                "estado_visual": "En curso",
                "color": "success",
                "acciones_disponibles": ["ver"],
                "puede_modificar": False,
                "dias_restantes": dias_hasta_fin
            }
    
    # Estado desconocido
    else:
        return {
            "estado_visual": "Desconocido",
            "color": "secondary",
            "acciones_disponibles": ["ver"],
            "puede_modificar": False
        }

def obtener_detalles_suspension_completos(suspension):
    """
    Obtiene los detalles completos de una suspensión incluyendo estado calculado
    ✅ CORREGIDO: Convierte fechas UTC a hora local de Lima para mostrar al usuario
    """
    estado_info = calcular_estado_suspension(suspension)
    
    # ✅ Convertir fechas UTC a hora local de Lima para mostrar al usuario
    fecha_creacion_lima = convert_utc_to_local(suspension.fecha_creacion) if suspension.fecha_creacion else None
    fecha_modificacion_lima = convert_utc_to_local(suspension.fecha_modificacion) if suspension.fecha_modificacion else None
    
    return {
        "id_suspension": suspension.id_suspension,
        "id_cliente": suspension.id_cliente,
        "id_inscripcion": suspension.id_inscripcion,
        "motivo": suspension.motivo,
        "fecha_inicio": suspension.fecha_inicio,        # Ya está en Lima local
        "fecha_fin": suspension.fecha_fin,              # Ya está en Lima local
        "archivo": suspension.archivo,
        "fecha_creacion": fecha_creacion_lima,          # ✅ Convertida de UTC a Lima
        "creado_por": suspension.creado_por,
        "fecha_modificacion": fecha_modificacion_lima,  # ✅ Convertida de UTC a Lima
        "modificado_por": suspension.modificado_por,
        "estado_bd": suspension.estado,
        "estado_visual": estado_info["estado_visual"],
        "color": estado_info["color"],
        "acciones_disponibles": estado_info["acciones_disponibles"],
        "puede_modificar": estado_info["puede_modificar"],
        "dias_restantes": estado_info.get("dias_restantes"),
        "mensaje": estado_info.get("mensaje")
    }