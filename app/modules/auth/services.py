#from app.modules.auth.models import Usuario
from app.core.db import engine
from app.core.enums import TipoUsuario
from passlib.context import CryptContext
from sqlmodel import Session
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)