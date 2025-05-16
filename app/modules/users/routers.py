from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
<<<<<<< Updated upstream
from app.modules.users.models import Administrador
from app.core.db import get_session
from app.modules.auth.models import Usuario, UsuarioRead
from app.modules.users.dependencies import get_current_admin  
=======
>>>>>>> Stashed changes
from typing import List

from app.core.db import get_session
from app.core.enums import TipoUsuario

from app.modules.users.models import Usuario, Administrador
from app.modules.users.schemas import UserCreate, UsuarioRead
from app.modules.users.services import crear_cliente
from app.modules.users.dependencies import get_current_admin


router = APIRouter()

@router.post("/administradores")
def crear_administrador(id_usuario: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    admin_existente = session.exec(
        select(Administrador).where(Administrador.id_usuario == id_usuario)
    ).first()
    if admin_existente:
        raise HTTPException(status_code=400, detail="Ya es administrador")

    nuevo_admin = Administrador(id_usuario=id_usuario)
    session.add(nuevo_admin)
    session.commit()
    session.refresh(nuevo_admin)
    return {"msg": "Administrador creado", "id_administrador": nuevo_admin.id_administrador}


<<<<<<< Updated upstream
=======

@router.post("/registrar-cliente")
def registrar_cliente(
    datos: UserCreate,
    db: Session = Depends(get_session)
):
    try:
        return crear_cliente(db=db, datos=datos, creado_por="sistema")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


>>>>>>> Stashed changes
@router.get(
    "/clientes",
    response_model=List[UsuarioRead],
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