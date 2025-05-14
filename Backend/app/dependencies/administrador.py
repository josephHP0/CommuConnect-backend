from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from app.models.administrador import Administrador
from app.db import get_session
from app.dependencies.auth import get_current_user

def get_current_admin(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    admin = session.exec(
        select(Administrador).where(Administrador.id_usuario == current_user.id_usuario)
    ).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return current_user
