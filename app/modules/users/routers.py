from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.modules.users.models import Administrador
from app.core.db import get_session
from app.modules.auth.models import Usuario, UsuarioRead
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


@router.get(
    "/clientes",
    response_model=List[UsuarioRead],
    dependencies=[Depends(get_current_admin)],
    summary="Listado de clientes (solo administradores)"
)
def listar_clientes(session: Session = Depends(get_session)):
    """
    Devuelve todos los usuarios que **no** son administradores.
    """
    clientes = session.exec(
        select(Usuario).where(Usuario.administrador == None)
    ).all()
    return clientes
