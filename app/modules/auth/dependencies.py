from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.users.models import Cliente, Usuario
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
        user_id: int = payload.get("sub") # type: ignore
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(Usuario).where(Usuario.id_usuario == user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_cliente_id(
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> int:
    # Busca el cliente asociado al usuario autenticado
    cliente = session.exec(
        select(Cliente).where(Cliente.id_usuario == current_user.id_usuario)
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente.id_cliente # type: ignore
