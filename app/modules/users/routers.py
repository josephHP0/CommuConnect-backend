from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.db import get_session
from app.modules.users.schemas import AdministradorCreate, AdministradorRead, ClienteCreate, ClienteRead, UsuarioCreate, UsuarioRead
from app.modules.users.services import crear_administrador, crear_cliente, crear_usuario

router = APIRouter()

@router.post("/usuario", response_model=UsuarioRead)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_session)):
    try:
        return crear_usuario(db, usuario)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")

@router.post("/cliente", response_model=ClienteRead)
def registrar_cliente(cliente: ClienteCreate, db: Session = Depends(get_session)):
    try:
        return crear_cliente(db, cliente)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar cliente: {str(e)}")

@router.post("/administrador", response_model=AdministradorRead)
def registrar_administrador(administrador: AdministradorCreate, db: Session = Depends(get_session)):
    try:
        return crear_administrador(db, administrador)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar administrador: {str(e)}")

