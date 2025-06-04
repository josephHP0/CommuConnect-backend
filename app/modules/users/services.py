from sqlmodel import Session, select
from app.core.enums import TipoUsuario
from app.modules.users.models import Administrador, Usuario, Cliente
from app.modules.users.schemas import ClienteCreate, UsuarioBase, UsuarioCreate, AdministradorCreate
from app.core.security import hash_password,create_confirmation_token
from utils.email_brevo import send_confirmation_email
from fastapi import HTTPException, status, BackgroundTasks
from datetime import datetime
from passlib.context import CryptContext
from app.modules.communities.schemas import ComunidadContexto
from app.modules.services.schemas import ServicioResumen
from app.modules.communities.services import obtener_servicios_de_comunidad
from typing import List, Optional, Dict
from app.modules.communities.models import ClienteXComunidad, Comunidad
from app.modules.billing.models import Inscripcion
import base64


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def crear_usuario(db: Session, usuario: UsuarioCreate):
    hashed_password = pwd_context.hash(usuario.password)
    db_usuario = Usuario(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        password=hashed_password,
        tipo=usuario.tipo, # type: ignore
        creado_por="sistema",
        estado=False
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def crear_cliente(db: Session, cliente: ClienteCreate, bg: BackgroundTasks):
    usuario_data = UsuarioCreate(
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        email=cliente.email,
        password=cliente.password,
        tipo=TipoUsuario.Cliente
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


def tiene_membresia_activa(session: Session, id_cliente: int, id_comunidad: int) -> str:
    inscripcion = session.exec(
        select(Inscripcion).where(
            Inscripcion.id_cliente == id_cliente,
            Inscripcion.id_comunidad == id_comunidad,
            Inscripcion.estado == 1
        )
    ).first()

    return "activa" if inscripcion else "inactiva"

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

            servicios_resumen = [ServicioResumen(nombre=s.nombre) for s in servicios]

            # 🔹 Determinar el estado de membresía individualmente
            estado = tiene_membresia_activa(session, id_cliente, comunidad.id_comunidad)

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

