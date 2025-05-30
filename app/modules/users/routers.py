from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id
from app.modules.communities.services import unir_cliente_a_comunidad
from app.modules.users.schemas import AdministradorCreate, AdministradorRead, ClienteCreate, ClienteRead, UsuarioCreate, UsuarioRead,UsuarioBase
from app.modules.users.services import crear_administrador, crear_cliente, crear_usuario, reenviar_confirmacion
from app.modules.users.dependencies import get_current_admin
from app.core.logger import logger
from typing import List
from app.modules.users.models import Usuario
from app.core.enums import TipoUsuario
from app.core.security import verify_confirmation_token

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
def registrar_cliente(cliente: ClienteCreate,  bg: BackgroundTasks, db: Session = Depends(get_session)):
    try:
        nuevo_cliente = crear_cliente(db, cliente, bg)
        logger.info(f"Cliente registrado: {cliente.email}")
        return nuevo_cliente
    except Exception as e:  # TEMPORAL para ver en consola
        logger.error(f"Error al registrar cliente {cliente.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar cliente")

@router.get("/confirm/{token}", response_model=UsuarioRead)
def confirmar_email(token: str, db: Session = Depends(get_session)):
    """
    Endpoint llamado por el frontend: /confirmar/:token
    Marca el usuario como activo si el token es válido.
    """
    email = verify_confirmation_token(token)
    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enlace inválido o expirado")

    usuario: Usuario | None = db.exec(select(Usuario).where(Usuario.email == email)).first()
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if usuario.estado:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya confirmado")

    usuario.estado = True
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    logger.info(f"Usuario {usuario.email} confirmado")
    return usuario

@router.post("/resend-confirmation")
def resend_confirmation(email: str,bg: BackgroundTasks,db: Session = Depends(get_session)):
    return reenviar_confirmacion(db, email, bg)


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

#Endpoint para regisrar a un cliente a una comunidad
@router.post("/unir_cliente_comunidad")
def unir_cliente_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id)
):
    return unir_cliente_a_comunidad(session, id_cliente, id_comunidad)


