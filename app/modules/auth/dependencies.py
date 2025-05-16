from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session, select

from app.core.db import get_session
<<<<<<< Updated upstream
=======
import os
>>>>>>> Stashed changes
from app.core.security import decode_access_token  # <— importa la función
from app.modules.users.models import Usuario 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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
        # Usa la función que ya conoce SECRET_KEY/ALGORITHM
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        # Asegura que venga como string
        if not isinstance(user_id, str):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Convierte a int para la consulta
    user = session.exec(
        select(Usuario).where(Usuario.id_usuario == int(user_id))
    ).first()
    if not user:
        raise credentials_exception
    return user
