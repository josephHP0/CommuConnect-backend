from app.models.usuario import Usuario
from app.db import engine
from passlib.context import CryptContext
from sqlmodel import Session
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def register_user(nombre: str, apellido: str, email: str, password: str, creado_por: str):
    hashed_password = hash_password(password)
    
    new_user = Usuario(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password=hashed_password,
        fecha_creacion=datetime.now(),
        creado_por=creado_por,
        estado=True
    )

    # Guardar en la base de datos
    with Session(engine) as session:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user
