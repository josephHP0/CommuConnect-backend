from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.users.schemas import AdministradorCreate, AdministradorRead, ClienteCreate, ClienteRead, UsuarioCreate, UsuarioRead,UsuarioBase
from app.modules.users.services import crear_administrador, crear_cliente, crear_usuario
from app.modules.users.dependencies import get_current_admin
from app.core.logger import logger
from typing import List
from app.modules.users.models import Usuario
from app.core.enums import TipoUsuario

router = APIRouter()

@router.post("/usuario", response_model=UsuarioRead)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_session)):
    try:
        nuevo_usuario = crear_usuario(db, usuario)
        logger.info(f"Usuario registrado: {usuario.email}")
        return nuevo_usuario
    except Exception as e:
        logger.error(f"Error al registrar usuario {usuario.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario")

@router.post("/cliente", response_model=ClienteRead)
def registrar_cliente(cliente: ClienteCreate, db: Session = Depends(get_session)):
    try:
        nuevo_cliente = crear_cliente(db, cliente)
        logger.info(f"Cliente registrado: {cliente.email}")
        return nuevo_cliente
    except Exception as e:  # TEMPORAL para ver en consola
        logger.error(f"Error al registrar cliente {cliente.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar cliente")

@router.post("/administrador", response_model=AdministradorRead)
def registrar_administrador(administrador: AdministradorCreate, db: Session = Depends(get_session)):
    try:
        nuevo_admin = crear_administrador(db, administrador)
        logger.info(f"Administrador registrado: {administrador.email}")
        return nuevo_admin
    except Exception as e:
        logger.error(f"Error al registrar administrador {administrador.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar administrador")


@router.get(
    "/clientes",
    response_model=List[UsuarioBase],
    summary="Listado de clientes (solo administradores)"
)
def listar_clientes(
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin),
):
    """
    Devuelve todos los usuarios cuyo tipo sea 'Cliente'.
    Acceso restringido a administradores.
    """
    clientes = session.exec(
        select(Usuario).where(Usuario.tipo == TipoUsuario.Cliente)
    ).all()
    return clientes