from sqlmodel import Session, select
from app.core.enums import TipoUsuario
from app.modules.geography.models import Departamento, Distrito
from app.modules.users.models import Administrador, Usuario, Cliente
from app.modules.users.schemas import ClienteCreate, ClienteUpdate, ClienteUsuarioFull, UsuarioBase, UsuarioCreate, AdministradorCreate
from app.core.security import hash_password,create_confirmation_token
from utils.email_brevo import send_confirmation_email
from fastapi import HTTPException, UploadFile, status, BackgroundTasks
from datetime import datetime
from passlib.context import CryptContext
from app.modules.communities.schemas import ComunidadContexto
from app.modules.services.schemas import ProfesionalCreate, ServicioResumen
from app.modules.communities.services import obtener_servicios_de_comunidad
from typing import List, Optional, Dict
from app.modules.communities.models import ClienteXComunidad, Comunidad
from app.modules.billing.models import Inscripcion
import base64
import pandas as pd
from io import BytesIO
from datetime import timedelta
from app.core.security import create_access_token, hash_password, decode_access_token
from utils.email_brevo import send_reset_link_email, send_password_changed_email
from jose import JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def crear_usuario(db: Session, usuario: UsuarioCreate):
    hashed_password = pwd_context.hash(usuario.password)
    
    # Robustly get the value whether it's an enum or a string
    tipo_value = usuario.tipo.value if isinstance(usuario.tipo, TipoUsuario) else usuario.tipo
    
    db_usuario = Usuario(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        password=hashed_password,
        tipo=tipo_value, # type: ignore
        creado_por="sistema",
        estado=False
    )
    db.add(db_usuario)
    db.flush() 
    return db_usuario

def crear_cliente(db: Session, cliente: ClienteCreate, bg: BackgroundTasks):
    usuario_data = UsuarioCreate(
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        email=cliente.email,
        password=cliente.password,
        tipo=TipoUsuario.Cliente,
    )
    nuevo_usuario = crear_usuario(db, usuario_data)

    db_cliente = Cliente(
        id_usuario=nuevo_usuario.id_usuario, # type: ignore
        tipo_documento=cliente.tipo_documento,
        num_doc=cliente.num_doc,
        numero_telefono=cliente.numero_telefono,
        id_departamento=cliente.id_departamento,
        id_distrito=cliente.id_distrito,
        direccion=cliente.direccion,
        fecha_nac=cliente.fecha_nac,
        genero=cliente.genero,
        talla=cliente.talla,
        peso=cliente.peso,
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    db.refresh(nuevo_usuario)
    token = create_confirmation_token(nuevo_usuario.email)
    bg.add_task(send_confirmation_email, nuevo_usuario.email, token)
    return db_cliente


def reenviar_confirmacion(db: Session, email: str, bg: BackgroundTasks):
    usuario: Usuario | None = db.exec(
        select(Usuario).where(Usuario.email == email)
    ).first()

    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")

    if usuario.estado:
        raise HTTPException(400, "La cuenta ya está confirmada")

    token = create_confirmation_token(usuario.email)
    bg.add_task(send_confirmation_email, usuario.email, token)
    return {"msg": "Se envió un nuevo enlace de confirmación"}

def crear_administrador(db: Session, administrador: AdministradorCreate):
    usuario_data = UsuarioCreate(
        nombre=administrador.nombre,
        apellido=administrador.apellido,
        email=administrador.email,
        password=administrador.password,
        tipo=TipoUsuario.Administrador
    )
    nuevo_usuario = crear_usuario(db, usuario_data)

    db_admin = Administrador(id_usuario=nuevo_usuario.id_usuario) # type: ignore
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    db.refresh(nuevo_usuario)
    return db_admin




def obtener_cliente_desde_usuario(session: Session, user: Usuario) -> Cliente:
    print(f" Buscando cliente con id_usuario = {user.id_usuario}...")

    try:
        cliente = session.exec(
            select(Cliente).where(Cliente.id_usuario == user.id_usuario)
        ).first()
        print(f"Cliente encontrado: {cliente}") if cliente else print("⚠️ Cliente no encontrado.")
    except Exception as e:
        print(f"Error al ejecutar la consulta del cliente: {e}")
        raise HTTPException(status_code=500, detail=f"[cliente] Error en la consulta: {str(e)}")

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return cliente


def obtener_comunidades_del_cliente(session: Session, id_cliente: int) -> List[Comunidad]:
    print(f"Buscando comunidades para el cliente con ID {id_cliente}...")

    try:
        comunidad_ids = session.exec(
            select(ClienteXComunidad.id_comunidad).where(
                ClienteXComunidad.id_cliente == id_cliente
            )
        ).all()
        print(f" IDs de comunidades encontradas: {comunidad_ids}")
    except Exception as e:
        print(f"Error al obtener IDs de comunidades: {e}")
        raise HTTPException(status_code=500, detail=f"[comunidades] Error al obtener IDs: {str(e)}")

    if not comunidad_ids:
        print(" No se encontraron comunidades para este cliente.")
        return []

    try:
        comunidades = session.exec(
            select(Comunidad).where(
                Comunidad.id_comunidad.in_(comunidad_ids), # type: ignore
                Comunidad.estado == True
            )
        ).all()
        print(f"Comunidades activas encontradas: {[c.nombre for c in comunidades]}")
    except Exception as e:
        print(f"Error al obtener detalles de comunidades: {e}")
        raise HTTPException(status_code=500, detail=f"[comunidades] Error al obtener comunidades activas: {str(e)}")

    return comunidades # type: ignore


def tiene_membresia_activa(session: Session, id_cliente: int, id_comunidad: int) -> int:
    inscripcion = session.exec(
        select(Inscripcion)
        .where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad
        )
        .order_by(Inscripcion.fecha_creacion.desc()) # type: ignore
    ).first()
    # Si no hay inscripción, puedes retornar None o un valor especial si lo deseas
    return inscripcion.estado if inscripcion else None # type: ignore

def construir_respuesta_contexto(
    session: Session,
    comunidades: List[Comunidad],
    id_cliente: int
) -> List[ComunidadContexto]:
    respuesta = []

    for comunidad in comunidades:
        print(f"Procesando comunidad ID {comunidad.id_comunidad}: {comunidad.nombre}")

        try:
            servicios = obtener_servicios_de_comunidad(session, comunidad.id_comunidad) # type: ignore
            print(f"Servicios obtenidos para '{comunidad.nombre}': {[s.nombre for s in servicios]}")

            servicios_resumen = [ServicioResumen(nombre=s.nombre,modalidad=s.modalidad) for s in servicios]

            # 🔹 Determinar el estado de membresía individualmente
            estado = tiene_membresia_activa(session, id_cliente, comunidad.id_comunidad) # type: ignore

            comunidad_contexto = ComunidadContexto.from_orm_with_base64(
                comunidad=comunidad,
                servicios=servicios_resumen,
                estado_membresia=estado
            )
            respuesta.append(comunidad_contexto)

        except Exception as e:
            print(f" Error al procesar comunidad ID {comunidad.id_comunidad}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error en comunidad '{comunidad.nombre}': {str(e)}"
            )

    return respuesta


def modificar_cliente(db: Session, id_usuario: int, data: dict, current_admin):
    cliente = db.exec(select(Cliente).where(Cliente.id_usuario == id_usuario)).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    usuario = db.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    password = data.pop("password", None)

    for campo, valor in data.items():
        if valor is not None:
            if hasattr(usuario, campo):
                setattr(usuario, campo, valor)
            elif hasattr(cliente, campo):
                setattr(cliente, campo, valor)


    if password:
        usuario.password = hash_password(password)

    usuario.fecha_modificacion = datetime.utcnow()
    usuario.modificado_por = current_admin.email

    db.commit()
    db.refresh(cliente)
    return cliente


# def obtener_cliente_con_usuario_por_id(db: Session, id_cliente: int):
#     cliente = db.exec(
#         select(Cliente).where(Cliente.id_cliente == id_cliente)
#     ).first()

#     if not cliente:
#         raise HTTPException(status_code=404, detail="Cliente no encontrado")

#     return cliente


def obtener_cliente_con_usuario_por_id(db: Session, id_cliente: int):
    cliente = db.exec(
        select(Cliente).where(Cliente.id_cliente == id_cliente)
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener nombres de departamento y distrito
    departamento = db.get(Departamento, cliente.id_departamento)
    distrito = db.get(Distrito, cliente.id_distrito)

    # Obtener usuario relacionado
    usuario = db.get(Usuario, cliente.id_usuario)

    # Construir el esquema con los nombres
    return ClienteUsuarioFull(
        id_cliente=cliente.id_cliente, # type: ignore
        tipo_documento=cliente.tipo_documento,
        num_doc=cliente.num_doc,
        numero_telefono=cliente.numero_telefono,
        id_departamento=cliente.id_departamento,
        departamento_nombre=departamento.nombre if departamento else None,
        id_distrito=cliente.id_distrito,
        distrito_nombre=distrito.nombre if distrito else None,
        direccion=cliente.direccion,
        fecha_nac=cliente.fecha_nac,
        genero=cliente.genero,
        talla=cliente.talla,
        peso=cliente.peso,
        usuario=usuario # type: ignore
    )

def procesar_archivo_clientes(db: Session, archivo: UploadFile, creado_por: str):
    df = pd.read_excel(BytesIO(archivo.file.read()), engine="openpyxl")

    resumen = {
        "insertados": 0,
        "omitidos": 0,
        "errores": []
    }

    for idx, fila in df.iterrows():
        try:
            if pd.isna(fila['email']) or pd.isna(fila['num_doc']): # type: ignore
                resumen["omitidos"] += 1
                continue

            # Verifica unicidad de email y num_doc
            existe_email = db.exec(select(Usuario).where(Usuario.email == fila['email'])).first()
            existe_doc = db.exec(select(Cliente).where(Cliente.num_doc == fila['num_doc'])).first()
            if existe_email or existe_doc:
                resumen["omitidos"] += 1
                continue

            usuario = Usuario(
                nombre=fila['nombre'], # type: ignore
                apellido=fila['apellido'], # type: ignore
                email=fila['email'], # type: ignore
                password=hash_password(fila['password']), # type: ignore
                tipo="Cliente", # type: ignore
                fecha_creacion=datetime.utcnow(),
                creado_por=creado_por,
                estado=True
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)

            cliente = Cliente(
                id_usuario=usuario.id_usuario, # type: ignore
                tipo_documento=fila['tipo_documento'], # type: ignore
                num_doc=fila['num_doc'], # type: ignore
                numero_telefono=fila['numero_telefono'], # type: ignore
                id_departamento=int(fila['id_departamento']), # type: ignore
                id_distrito=int(fila['id_distrito']), # type: ignore
                direccion=fila.get('direccion'),
                fecha_nac=fila['fecha_nac'], # type: ignore
                genero=fila.get('genero'),
                talla=float(fila['talla']), # type: ignore
                peso=float(fila['peso']) # type: ignore
            )
            db.add(cliente)
            db.commit()

            resumen["insertados"] += 1

        except Exception as e:
            db.rollback()
            resumen["errores"].append(f"Fila {idx + 2}: {str(e)}") # type: ignore

    return resumen

"""sercies cambio de contraseña"""
RESET_LINK_EXPIRATION_MINUTES = 5
FRONTEND_RESET_URL = "http://localhost:4200/autenticacion/reset-password"



def solicitar_recuperacion_contrasena_con_link(db: Session, email: str, bg: BackgroundTasks) -> dict:
    """
    Solicita recuperación de contraseña por enlace (token JWT).
    Si el correo existe, envía un link con token válido por 30 minutos.
    """
    usuario = obtener_usuario_activo_por_email(db, email)

    if not usuario:
        return {
            "mensaje": "El correo no está registrado en el sistema.",
            "email_enviado": False
        }

    # Crear token válido por 30 minutos
    expires_delta = timedelta(minutes=RESET_LINK_EXPIRATION_MINUTES)
    token = create_access_token(
        subject=email,
        extra_claims={"tipo": "reset_password"},
        expires_delta=expires_delta
    )

    # Enlace con token
    link = f"{FRONTEND_RESET_URL}?token={token}"

    try:
        bg.add_task(send_reset_link_email, usuario.email, usuario.nombre, link)
        return {
            "mensaje": "Enlace de recuperación enviado con éxito. La vigencia de enlace es de 5 minutos",
            "email_enviado": True,
            "token": token  # ✅ Coma agregada arriba
        }
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return {
            "mensaje": "No se pudo enviar el correo de recuperación.",
            "email_enviado": False
        }

def obtener_usuario_activo_por_email(db: Session, email: str) -> Optional[Usuario]:
    """Devuelve un usuario activo si existe, sino None."""
    return db.exec(
        select(Usuario).where(Usuario.email == email, Usuario.estado == True)
    ).first()


def verificar_token_reset_password(token: str) -> dict:
    """
    Verifica si un token es válido y corresponde a recuperación de contraseña
    """
    try:
        payload = decode_access_token(token)

        if payload.get("tipo") != "reset_password":
            return {
                "valido": False,
                "mensaje": "El token no es para recuperación de contraseña."
            }

        return {
            "valido": True,
            "mensaje": "Token válido."
        }

    except JWTError:
        return {
            "valido": False,
            "mensaje": "El enlace ya expiró o es inválido."
        }

def cambiar_contrasena_con_link(db: Session, token: str, nueva_contrasena: str, bg: BackgroundTasks) -> dict:
    try:
        payload = decode_access_token(token)

        if payload.get("tipo") != "reset_password":
            return {"mensaje": "El enlace no es válido para cambiar la contraseña.", "exito": False}

        email = payload.get("sub")
        if not email:
            return {"mensaje": "El enlace está incompleto. Intenta solicitar uno nuevo.", "exito": False}

        usuario = db.exec(
            select(Usuario).where(Usuario.email == email, Usuario.estado == True)
        ).first()

        if not usuario:
            return {"mensaje": "No se encontró una cuenta activa asociada al enlace.", "exito": False}

        # Cambiar la contraseña
        usuario.password = hash_password(nueva_contrasena)
        usuario.fecha_modificacion = datetime.utcnow()
        usuario.modificado_por = "Sistema - Recuperación"

        db.add(usuario)
        db.commit()

        bg.add_task(send_password_changed_email, usuario.email, usuario.nombre)


        return {"mensaje": "Tu contraseña fue actualizada correctamente.", "exito": True}

    except Exception as e:
        print(f"Error en cambiar_contrasena_con_link: {e}")
        return {"mensaje": "El enlace ya expiró o es inválido. Solicita uno nuevo.", "exito": False}