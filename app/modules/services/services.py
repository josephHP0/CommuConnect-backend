from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select, func
from app.modules.services.models import  Servicio, Profesional
from app.modules.reservations.models import SesionVirtual,Sesion, Reserva,SesionPresencial  
from typing import List, Optional
from app.modules.geography.models import Distrito  # Modelo de geografía
from app.modules.services.models import Local, Profesional      # Modelo Local dentro de services
from app.modules.services.schemas import DistritoOut, ServicioCreate, ServicioRead, ServicioUpdate  # Esquema de salida (DTO)
import base64
from app.modules.services.schemas import ProfesionalCreate, ProfesionalOut, SesionVirtualConDetalle, SesionPresencialConDetalle
from app.modules.services.schemas import InscritoPresencialDetalleOut
import pandas as pd
from .schemas import DetalleSesionVirtualResponse, LocalCreate, ProfesionalDetalleOut, InscritoDetalleOut,DetalleSesionPresencialResponse,LocalDetalleOut
from app.modules.users.models import Cliente, Usuario
from app.modules.communities.models import Comunidad
from io import BytesIO
import numpy as np
from app.modules.reservations.schemas import SesionPresencialCargaMasiva


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
    df = pd.read_excel(BytesIO(archivo.file.read()), engine="openpyxl")

    resumen = {
        "insertados": 0,
        "omitidos": 0,
        "errores": []
    }

    for idx, fila in df.iterrows():
        try:
            email = str(fila.get("email")).strip().lower()

            if pd.isna(email) or email == "":
                resumen["errores"].append(f"Fila {idx + 2}: El email está vacío")
                resumen["omitidos"] += 1
                continue

            existe = db.exec(select(Profesional).where(Profesional.email == email)).first()
            if existe:
                resumen["errores"].append(f"Fila {idx + 2}: El email '{email}' ya existe")
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


def obtener_sesiones_virtuales_por_profesional(
    db: Session, id_profesional: int
) -> List[SesionVirtualConDetalle]:
    sesiones_virtuales = db.exec(
        select(SesionVirtual).where(SesionVirtual.id_profesional == id_profesional)
    ).all()

    resultado = []

    for sv in sesiones_virtuales:
        sesion = db.exec(
            select(Sesion).where(Sesion.id_sesion == sv.id_sesion)
        ).first()

        if sesion:
            inscritos_resultado = db.exec(
                select(func.count(Reserva.id_reserva)).where(Reserva.id_sesion == sesion.id_sesion)
            ).one()

            inscritos = inscritos_resultado[0] if isinstance(inscritos_resultado, tuple) else inscritos_resultado

            resultado.append(SesionVirtualConDetalle(
                id_sesion_virtual=sv.id_sesion_virtual,
                id_sesion=sesion.id_sesion,
                fecha=sesion.inicio.date() if sesion.inicio else None,
                hora_inicio=sesion.inicio.time() if sesion.inicio else None,
                hora_fin=sesion.fin.time() if sesion.fin else None,
                inscritos=inscritos
            ))

    return resultado


def get_sesion_presencial_con_local(id_sesion_presencial: int, db: Session):
    sp = db.exec(
        select(SesionPresencial)
        .where(SesionPresencial.id_sesion_presencial == id_sesion_presencial)
    ).first()

    if not sp:
        raise HTTPException(status_code=404, detail="Sesión presencial no encontrada")

    sesion = db.get(Sesion, sp.id_sesion)
    local = db.get(Local, sp.id_local)

    return sp, sesion, local





def obtener_detalle_sesion_virtual(id_sesion_virtual: int, db: Session) -> DetalleSesionVirtualResponse:
    sv, sesion, profesional = get_sesion_virtual_con_profesional(id_sesion_virtual, db)

    profesional_out = formatear_profesional(profesional)
    inscritos_out = listar_inscritos_de_sesion(sv.id_sesion, db)

    return DetalleSesionVirtualResponse(
        id_sesion_virtual=sv.id_sesion_virtual,
        descripcion=sesion.descripcion,
        fecha=sesion.inicio.date() if sesion.inicio else None,
        hora_inicio=sesion.inicio.time() if sesion.inicio else None,
        hora_fin=sesion.fin.time() if sesion.fin else None,
        profesional=profesional_out,
        inscritos=inscritos_out
    )
def formatear_local(local: Local) -> LocalDetalleOut:
    return LocalDetalleOut(
        nombre=local.nombre,
        direccion_detallada=local.direccion_detallada,
        responsable=local.responsable
    )


def obtener_detalle_sesion_presencial(id_sesion_presencial: int, db: Session) -> DetalleSesionPresencialResponse:
    # Obtener datos: SesionPresencial, Sesion, Local
    sp, sesion, local = get_sesion_presencial_con_local(id_sesion_presencial, db)

    # Formatear local
    local_out = formatear_local(local)

    # Listar inscritos
    inscritos_out = listar_inscritos_presencial(sp.id_sesion, db)

    return DetalleSesionPresencialResponse(
        id_sesion_presencial=sp.id_sesion_presencial,
        descripcion=sesion.descripcion,
        fecha=sesion.inicio.date() if sesion.inicio else None,
        hora_inicio=sesion.inicio.time() if sesion.inicio else None,
        hora_fin=sesion.fin.time() if sesion.fin else None,
        local=local_out,
        inscritos=inscritos_out
    )



def obtener_sesiones_presenciales_por_local(
    db: Session, id_local: int
) -> List[SesionPresencialConDetalle]:
    sesiones_presenciales = db.exec(
        select(SesionPresencial).where(SesionPresencial.id_local == id_local)
    ).all()

    resultado = []

    for sp in sesiones_presenciales:
        sesion = db.exec(
            select(Sesion).where(Sesion.id_sesion == sp.id_sesion)
        ).first()

        if sesion:
            inscritos_resultado = db.exec(
                select(func.count(Reserva.id_reserva)).where(Reserva.id_sesion == sesion.id_sesion)
            ).one()

            inscritos = inscritos_resultado[0] if isinstance(inscritos_resultado, tuple) else inscritos_resultado

            resultado.append(SesionPresencialConDetalle(
                id_sesion_presencial=sp.id_sesion_presencial,
                id_sesion=sesion.id_sesion,
                fecha=sesion.inicio.date() if sesion.inicio else None,
                hora_inicio=sesion.inicio.time() if sesion.inicio else None,
                hora_fin=sesion.fin.time() if sesion.fin else None,
                capacidad=sp.capacidad,                     # ✅ nuevo campo
                inscritos=inscritos
            ))

    return resultado


def get_sesion_virtual_con_profesional(id_sesion_virtual: int, db: Session):
    sv = db.get(SesionVirtual, id_sesion_virtual)
    if not sv:
        raise HTTPException(status_code=404, detail="Sesión virtual no encontrada")

    sesion = db.get(Sesion, sv.id_sesion)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión base no encontrada")

    profesional = db.get(Profesional, sv.id_profesional)
    if not profesional:
        raise HTTPException(status_code=404, detail="Profesional no encontrado")

    return sv, sesion, profesional


def formatear_profesional(profesional: Profesional) -> ProfesionalDetalleOut:
    if profesional.nombre_completo:
        partes = profesional.nombre_completo.strip().split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ""
    else:
        nombre, apellido = "", ""

    return ProfesionalDetalleOut(
        nombre=nombre,
        apellido=apellido,
        email=profesional.email
    )

def listar_inscritos_de_sesion(id_sesion: int, db: Session) -> List[InscritoDetalleOut]:
    reservas = db.exec(
        select(Reserva).where(Reserva.id_sesion == id_sesion)
    ).all()

    inscritos = []

    for reserva in reservas:
        cliente = db.get(Cliente, reserva.id_cliente)
        usuario = db.get(Usuario, cliente.id_usuario)
        comunidad = db.get(Comunidad, reserva.id_comunidad)

        inscritos.append(InscritoDetalleOut(
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            comunidad=comunidad.nombre,
            entrego_archivo=bool(reserva.archivo)
        ))

    return inscritos

def listar_inscritos_presencial(id_sesion: int, db: Session) -> List[InscritoPresencialDetalleOut]:
    reservas = db.exec(
        select(Reserva).where(Reserva.id_sesion == id_sesion)
    ).all()

    inscritos = []

    for reserva in reservas:
        cliente = db.get(Cliente, reserva.id_cliente)
        usuario = db.get(Usuario, cliente.id_usuario)
        comunidad = db.get(Comunidad, reserva.id_comunidad)

        inscritos.append(InscritoPresencialDetalleOut(
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            comunidad=comunidad.nombre
        ))

    return inscritos


def crear_local(
    db: Session,
    data: "LocalCreate",
    creado_por: str
) -> Local:
    local = Local(
        id_departamento=data.id_departamento,
        id_distrito=data.id_distrito,
        id_servicio=data.id_servicio,
        direccion_detallada=data.direccion_detallada,
        responsable=data.responsable,
        nombre=data.nombre,
        link=data.link,
        fecha_creacion=datetime.utcnow(),
        creado_por=creado_por,
        estado=1
    )
    db.add(local)
    db.commit()
    db.refresh(local)
    return local


def procesar_archivo_sesiones_presenciales(
    db: Session, archivo: UploadFile, id_servicio: int, creado_por: str
):
    df = pd.read_excel(BytesIO(archivo.file.read()), engine="openpyxl")
    df = df.replace({np.nan: None})

    resumen = {
        "insertados": 0,
        "errores": []
    }

    for idx, fila in df.iterrows():
        try:
            datos_dict = fila.to_dict()
            datos_dict["id_servicio"] = id_servicio
            
            valor_capacidad = datos_dict.get("capacidad")

            try:
                if valor_capacidad is None or str(valor_capacidad).strip() == '':
                    datos_dict["capacidad"] = None
                else:
                    datos_dict["capacidad"] = int(float(valor_capacidad))
            except (ValueError, TypeError):
                datos_dict["capacidad"] = None

                
            datos = SesionPresencialCargaMasiva.model_validate(datos_dict)
            procesar_fila_sesion_presencial(
                db=db,
                datos=datos,
                id_servicio=id_servicio,
                creado_por=creado_por,
                fila=idx + 2
            )
            resumen["insertados"] += 1
        except Exception as e:
            db.rollback()
            resumen["errores"].append(f"Fila {idx + 2}: {str(e)}")

    return resumen


def procesar_fila_sesion_presencial(
    db: Session,
    datos: SesionPresencialCargaMasiva,
    id_servicio: int,
    creado_por: str,
    fila: int
):
    ahora = datetime.now(timezone.utc)

    # Validar que el local exista y esté vinculado al servicio
    local = db.exec(
        select(Local).where(
            Local.id_local == datos.id_local,
            Local.id_servicio == id_servicio
        )
    ).first()

    if not local:
        raise ValueError(f"Fila {fila}: El local con ID {datos.id_local} no está asociado al servicio con ID {id_servicio}.")
    

    if datos.fecha_inicio.tzinfo is None:
        datos.fecha_inicio = datos.fecha_inicio.replace(tzinfo=timezone.utc)
    if datos.fecha_fin.tzinfo is None:
        datos.fecha_fin = datos.fecha_fin.replace(tzinfo=timezone.utc)
    if datos.capacidad is None or datos.capacidad <= 0:
        raise ValueError(f"Fila {fila}: La capacidad debe ser un número positivo.")
    if datos.fecha_inicio < ahora:
        raise ValueError(f"Fila {fila}: No se puede crear una sesión en el pasado.")
    if datos.fecha_inicio >= datos.fecha_fin:
        raise ValueError(f"Fila {fila}: La fecha de inicio debe ser anterior a la fecha de fin.")

    servicio = db.get(Servicio, datos.id_servicio)
    if not servicio or servicio.estado != 1:
        raise ValueError(f"Fila {fila}: Servicio con ID {datos.id_servicio} no existe o está inactivo.")
    if servicio.modalidad.lower() != "presencial":
        raise ValueError(f"Fila {fila}: El servicio {datos.id_servicio} no es presencial.")

    local = db.get(Local, datos.id_local)
    if not local or local.estado != 1:
        raise ValueError(f"Fila {fila}: Local con ID {datos.id_local} no existe o está inactivo.")
    if local.id_servicio != datos.id_servicio:
        raise ValueError(f"Fila {fila}: El local {datos.id_local} no está asignado al servicio {datos.id_servicio}.")

    

    validar_solapamiento_presencial(db, datos, fila)

    nueva_sesion = Sesion(
        id_servicio=datos.id_servicio,
        tipo="Presencial",
        descripcion=datos.descripcion or f"Sesión presencial de servicio {datos.id_servicio}",
        inicio=datos.fecha_inicio,
        fin=datos.fecha_fin,
        creado_por=creado_por,
        fecha_creacion=ahora,
        estado=1
    )
    db.add(nueva_sesion)
    db.flush()

    nueva_presencial = SesionPresencial(
        id_sesion=nueva_sesion.id_sesion,
        id_local=datos.id_local,
        capacidad=datos.capacidad,
        creado_por=creado_por,
        fecha_creacion=ahora,
        estado=1
    )
    db.add(nueva_presencial)
    db.commit()


def validar_solapamiento_presencial(db: Session, datos: SesionPresencialCargaMasiva, fila: int):
    conflicto = db.exec(
        select(Sesion)
        .join(SesionPresencial, Sesion.id_sesion == SesionPresencial.id_sesion)
        .where(
            Sesion.id_servicio == datos.id_servicio,
            SesionPresencial.id_local == datos.id_local,
            Sesion.inicio < datos.fecha_fin,
            Sesion.fin > datos.fecha_inicio
        )
    ).first()

    if conflicto:
        raise ValueError(
            f"Fila {fila}: Ya existe una sesión presencial para el servicio {datos.id_servicio} en el local {datos.id_local} "
            f"que se cruza con el horario del {datos.fecha_inicio} al {datos.fecha_fin}."
        )
