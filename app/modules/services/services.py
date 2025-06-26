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


def procesar_archivo_profesionales(db: Session, archivo: UploadFile, creado_por: str):
    df = pd.read_excel(archivo.file)

    resumen = {
        "insertados": 0,
        "omitidos": 0,
        "errores": []
    }

    for idx, fila in df.iterrows():
        try:
            email = str(fila.get("email")).strip().lower()

            if pd.isna(email) or email == "":
                resumen["omitidos"] += 1
                continue

            existe = db.exec(select(Profesional).where(Profesional.email == email)).first()
            if existe:
                resumen["omitidos"] += 1
                continue

            servicio_id = int(fila.get("id_servicio")) if not pd.isna(fila.get("id_servicio")) else None
            if servicio_id:
                servicio = db.exec(select(Servicio).where(Servicio.id_servicio == servicio_id)).first()
                if not servicio:
                    resumen["errores"].append(f"Fila {idx + 2}: servicio {servicio_id} no existe")
                    continue

            nuevo_profesional = Profesional(
                nombre_completo=str(fila.get("nombre_completo")).strip() if not pd.isna(fila.get("nombre_completo")) else None,
                email=email,
                id_servicio=servicio_id,
                formulario=str(fila.get("formulario")).strip() if not pd.isna(fila.get("formulario")) else None,
                creado_por=creado_por,
                fecha_creacion=datetime.utcnow(),
                estado=1
            )

            db.add(nuevo_profesional)
            db.commit()
            resumen["insertados"] += 1

        except Exception as e:
            db.rollback()
            resumen["errores"].append(f"Fila {idx + 2}: {str(e)}")

    return resumen

