from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from typing import Optional, Dict, Any

# Carga de secretos
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
CONFIRM_TOKEN_EXPIRE_HOURS  = int(os.getenv("CONFIRM_TOKEN_EXPIRE_HOURS", 24))

# Contexto bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str,extra_claims: Optional[Dict[str, Any]] = None, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un JWT con:
    - sub: subject (p. ej. user.id)
    - exp: fecha de expiración
    - + cualquier claim extra que pases en extra_claims
    """
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire
    }
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # type: ignore

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodifica y verifica un JWT.
    Lanza JWTError si no es válido o ha expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
        return payload
    except JWTError as e:
        raise


def create_confirmation_token(email: str) -> str:
    """
    JWT corto cuyo subject es el email del usuario.
    Se usa en el enlace /confirmar/<token>
    """
    now    = datetime.utcnow()
    expire = now + timedelta(hours=CONFIRM_TOKEN_EXPIRE_HOURS)
    payload = {"sub": email, "iat": now, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM) # type: ignore

def verify_confirmation_token(token: str) -> Optional[str]:
    """
    Devuelve el email si el token es válido, si no → None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
        return payload.get("sub")
    except JWTError:
        return None