from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select
from app.modules.services.models import  Servicio, Profesional
from app.modules.reservations.models import SesionVirtual,Sesion
from typing import List, Optional
from app.modules.geography.models import Distrito  # Modelo de geografía
from app.modules.services.models import Local      # Modelo Local dentro de services
from app.modules.services.schemas import DistritoOut, ServicioCreate, ServicioRead, ServicioUpdate  # Esquema de salida (DTO)
import base64
from app.modules.services.schemas import ProfesionalCreate, ProfesionalOut
import pandas as pd
from io import BytesIO

def obtener_servicios_por_ids(session: Session, servicio_ids: List[int]):
    if not servicio_ids:
        return []

    servicios = session.exec(
        select(Servicio).where(
            Servicio.id_servicio.in_(servicio_ids), # type: ignore
            Servicio.estado == True  # Solo servicios activos
        )
    ).all()

    return servicios

def register_user(user_data):
    # solo lo hice para que corra xd
    pass


def obtener_profesionales_por_servicio(session: Session, id_servicio: int):
    """
    Recupera todos los profesionales cuyo campo `id_servicio` coincide con el parámetro.
    Previamente, esta función buscaba a través de Sesion → SesionVirtual, pero como
    ahora `Profesional` lleva directamente `id_servicio`, podemos simplificar la consulta.
    """
    profesionales = session.exec(
        select(Profesional).where(Profesional.id_servicio == id_servicio)
    ).all()
    return profesionales


def obtener_distritos_por_servicio_service(session: Session, id_servicio: int) -> List[DistritoOut]:
    # Obtener locales activos
    locales = session.exec(
        select(Local).where(Local.id_servicio == id_servicio, Local.estado == 1)
    ).all()

    if not locales:
        return []

    distrito_ids = {local.id_distrito for local in locales if local.id_distrito is not None}

    distritos = session.exec(
        select(Distrito).where(Distrito.id_distrito.in_(distrito_ids))
    ).all()

    resultado = []
    for d in distritos:
        imagen = base64.b64encode(d.imagen).decode("utf-8") if d.imagen else None
        resultado.append(DistritoOut(
            id_distrito=d.id_distrito,
            nombre=d.nombre,
            imagen=imagen
        ))

    return resultado


def listar_servicios(db: Session) -> list[ServicioRead]:
    servicios = db.exec(select(Servicio)).all()
    resultado = []
    for servicio in servicios:
        servicio_dict = servicio.dict()
        if servicio.imagen:
            servicio_dict["imagen_base64"] = base64.b64encode(servicio.imagen).decode("utf-8")
        else:
            servicio_dict["imagen_base64"] = None
        resultado.append(ServicioRead(**servicio_dict))
    return resultado


def crear_servicio(
    db: Session,
    servicio_data: ServicioCreate,
    archivo_imagen: UploadFile,
    usuario: str = "admin"
):
    contenido_imagen = archivo_imagen.file.read() if archivo_imagen else None

    nuevo_servicio = Servicio(
        nombre=servicio_data.nombre,
        descripcion=servicio_data.descripcion,
        modalidad=servicio_data.modalidad,
        imagen=contenido_imagen,
        fecha_creacion=datetime.utcnow(),
        creado_por=usuario,
        estado=True,
    )

    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    return nuevo_servicio

def eliminar_servicio(db: Session, id_servicio: int, usuario: str = "admin"):
    servicio = db.get(Servicio, id_servicio)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    servicio.estado = False
    servicio.fecha_modificacion = datetime.now(timezone.utc)
    servicio.modificado_por = usuario

    db.add(servicio)
    db.commit()

def actualizar_servicio(
    db: Session,
    id_servicio: int,
    datos: ServicioUpdate,
    imagen: Optional[UploadFile] = None,
    usuario: str = "admin"
):
    servicio = db.get(Servicio, id_servicio)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    if datos.nombre is not None:
        servicio.nombre = datos.nombre
    if datos.descripcion is not None:
        servicio.descripcion = datos.descripcion
    if datos.modalidad is not None:
        servicio.modalidad = datos.modalidad
    if imagen is not None:
        servicio.imagen = imagen.file.read()

    servicio.fecha_modificacion = datetime.now(timezone.utc)
    servicio.modificado_por = usuario

    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio

def obtener_servicio_por_id(db: Session, id_servicio: int) -> ServicioRead:
    servicio = db.get(Servicio, id_servicio)
    if not servicio or not servicio.estado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    imagen_base64 = (
        base64.b64encode(servicio.imagen).decode("utf-8")
        if servicio.imagen else None
    )

    return ServicioRead(
        id_servicio=servicio.id_servicio,
        nombre=servicio.nombre,
        descripcion=servicio.descripcion,
        modalidad=servicio.modalidad,
        imagen_base64=imagen_base64,
        fecha_creacion=servicio.fecha_creacion,
        creado_por=servicio.creado_por,
        fecha_modificacion=servicio.fecha_modificacion,
        modificado_por=servicio.modificado_por,
        estado=servicio.estado
    )

def listar_profesionales(db: Session) -> list[Profesional]:
    return db.exec(select(Profesional).where(Profesional.estado == 1)).all()

def crear_profesional(db: Session, data: ProfesionalCreate, creado_por: str) -> Profesional:
    nuevo_profesional = Profesional(
        nombre_completo=data.nombre_completo,
        email=data.email,
        id_servicio=data.id_servicio,
        formulario=data.formulario,
        fecha_creacion=datetime.utcnow(),
        creado_por=creado_por,
        estado=1
    )
    db.add(nuevo_profesional)
    db.commit()
    db.refresh(nuevo_profesional)
    return nuevo_profesional


def listar_locales_por_servicio(db: Session, id_servicio: int) -> list[Local]:
    query = select(Local).where(
        Local.id_servicio == id_servicio,
        Local.estado == 1
    )
    return db.exec(query).all()

def procesar_archivo_locales(db: Session, archivo: UploadFile, id_servicio: int, creado_por: str):
    """
    Procesa un archivo Excel para cargar locales masivamente a un servicio específico.
    
    Estructura esperada del Excel (en este orden):
    - nombre: Nombre del local (obligatorio)
    - id_distrito: ID del distrito (obligatorio)
    - direccion_detallada: Dirección completa del local (obligatorio)
    - responsable: Persona responsable del local (opcional)
    - link: URL o enlace relacionado (opcional)
    
    Nota: El departamento se asigna automáticamente como 14 (por defecto)
    """
    df = pd.read_excel(BytesIO(archivo.file.read()), engine="openpyxl")

    resumen = {
        "insertados": 0,
        "omitidos": 0,
        "errores": []
    }

    # Verificar que el servicio existe
    servicio = db.get(Servicio, id_servicio)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    for idx, fila in df.iterrows():
        try:
            # Validar campos obligatorios
            if pd.isna(fila['nombre']) or pd.isna(fila['id_distrito']) or pd.isna(fila['direccion_detallada']) or fila['direccion_detallada'] == '':
                resumen["omitidos"] += 1
                continue

            # Verificar si ya existe un local con el mismo nombre para este servicio
            existe_local = db.exec(
                select(Local).where(
                    Local.nombre == fila['nombre'],
                    Local.id_servicio == id_servicio
                )
            ).first()
            
            if existe_local:
                resumen["omitidos"] += 1
                continue

            # Manejar campos opcionales
            responsable_valor = None
            if not pd.isna(fila.get('responsable')) and fila.get('responsable') != '':
                responsable_valor = fila['responsable']
            
            link_valor = None
            if not pd.isna(fila.get('link')) and fila.get('link') != '':
                link_valor = fila['link']

            # Crear nuevo local
            nuevo_local = Local(
                nombre=fila['nombre'],  # type: ignore
                direccion_detallada=fila['direccion_detallada'],  # type: ignore (ahora obligatorio)
                responsable=responsable_valor,
                link=link_valor,
                id_departamento=14,  # Departamento por defecto
                id_distrito=int(fila['id_distrito']),  # type: ignore
                id_servicio=id_servicio,
                fecha_creacion=datetime.utcnow(),
                creado_por=creado_por,
                estado=1
            )
            
            db.add(nuevo_local)
            db.commit()
            db.refresh(nuevo_local)

            resumen["insertados"] += 1

        except Exception as e:
            db.rollback()
            resumen["errores"].append(f"Fila {idx + 2}: {str(e)}")  # type: ignore

    return resumen

def procesar_archivo_sesiones_presenciales(db: Session, archivo: UploadFile, id_servicio: int, creado_por: str):
    """
    Procesa un archivo Excel para cargar sesiones presenciales masivamente a un servicio específico.
    
    Estructura esperada del Excel (en este orden):
    - id_local: ID del local donde se realizará la sesión (obligatorio)
    - fecha_inicio: Fecha y hora de inicio (formato: DD/MM/YYYY HH:MM) (obligatorio)
    - fecha_fin: Fecha y hora de fin (formato: DD/MM/YYYY HH:MM) (obligatorio)
    - capacidad: Capacidad máxima de la sesión (opcional)
    - descripcion: Descripción de la sesión (opcional)
    
    Nota: El tipo se asigna automáticamente como "Presencial"
    """
    from app.modules.reservations.models import Sesion, SesionPresencial
    from datetime import datetime
    
    df = pd.read_excel(BytesIO(archivo.file.read()), engine="openpyxl")

    resumen = {
        "insertados": 0,
        "omitidos": 0,
        "errores": []
    }

    # Verificar que el servicio existe
    servicio = db.get(Servicio, id_servicio)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    for idx, fila in df.iterrows():
        try:
            # Validar campos obligatorios
            if (pd.isna(fila['id_local']) or 
                pd.isna(fila['fecha_inicio']) or pd.isna(fila['fecha_fin'])):
                resumen["omitidos"] += 1
                continue

            # Convertir fechas
            try:
                if isinstance(fila['fecha_inicio'], str):
                    fecha_inicio = datetime.strptime(fila['fecha_inicio'], "%d/%m/%Y %H:%M")
                else:
                    fecha_inicio = fila['fecha_inicio']
                
                if isinstance(fila['fecha_fin'], str):
                    fecha_fin = datetime.strptime(fila['fecha_fin'], "%d/%m/%Y %H:%M")
                else:
                    fecha_fin = fila['fecha_fin']
            except ValueError as e:
                resumen["errores"].append(f"Fila {idx + 2}: Error en formato de fecha - {str(e)}")
                continue

            # Validar que la fecha de fin sea posterior a la de inicio
            if fecha_fin <= fecha_inicio:
                resumen["errores"].append(f"Fila {idx + 2}: La fecha de fin debe ser posterior a la de inicio")
                continue

            # Verificar que el local existe
            local = db.get(Local, int(fila['id_local']))
            if not local:
                resumen["errores"].append(f"Fila {idx + 2}: Local con ID {fila['id_local']} no encontrado")
                continue

            # Manejar descripción opcional
            descripcion_valor = "Sesión presencial"  # Valor por defecto
            if not pd.isna(fila['descripcion']) and fila['descripcion'] != '':
                descripcion_valor = fila['descripcion']

            # Crear nueva sesión
            nueva_sesion = Sesion(
                id_servicio=id_servicio,
                tipo="Presencial",
                descripcion=descripcion_valor,
                inicio=fecha_inicio,
                fin=fecha_fin,
                fecha_creacion=datetime.utcnow(),
                creado_por=creado_por,
                estado=True
            )
            
            db.add(nueva_sesion)
            db.flush()  # Para obtener el ID de la sesión

            # Manejar capacidad opcional
            capacidad_valor = None
            if not pd.isna(fila['capacidad']) and fila['capacidad'] != '':
                capacidad_valor = int(fila['capacidad'])

            # Crear sesión presencial asociada
            nueva_sesion_presencial = SesionPresencial(
                id_sesion=nueva_sesion.id_sesion,
                id_local=int(fila['id_local']),  # type: ignore
                capacidad=capacidad_valor,
                fecha_creacion=datetime.utcnow(),
                creado_por=creado_por,
                estado=True
            )
            
            db.add(nueva_sesion_presencial)
            db.commit()
            db.refresh(nueva_sesion)

            resumen["insertados"] += 1

        except Exception as e:
            db.rollback()
            resumen["errores"].append(f"Fila {idx + 2}: {str(e)}")  # type: ignore

    return resumen