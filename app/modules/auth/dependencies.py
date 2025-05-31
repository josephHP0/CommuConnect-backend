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
    print(f"\n[TOKEN RECIBIDO]: {token}")
    print("\n Entrando a get_current_user")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        print(f"Token recibido: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(" Token decodificado correctamente")
        user_id: int = payload.get("sub")
        print(f" ID extraído del token: {user_id}")
        if user_id is None:
            print(" 'sub' no presente en el token")
            raise credentials_exception
    except JWTError as e:
        print(f"Error al decodificar el token: {e}")
        raise credentials_exception

    try:
        user = session.exec(select(Usuario).where(Usuario.id_usuario == user_id)).first()
        if user is None:
            print(f" Usuario con ID {user_id} no existe en la base de datos")
            raise credentials_exception
        print(f"👤 Usuario autenticado: {user.email} (ID: {user.id_usuario})")
        return user
    except Exception as e:
        print(f"Error en consulta de usuario: {e}")
        raise credentials_exception


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
