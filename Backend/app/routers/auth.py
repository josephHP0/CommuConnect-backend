from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse, RegisterRequest
from app.auth import verify_password, create_access_token
from app.db import engine  # o como tengas tu conexión
from app.services.auth_service import register_user
from app.auth import create_access_token

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(Usuario).where(Usuario.email == data.email)).first()
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = create_access_token({"sub": str(user.id_usuario)})
        return {"access_token": token}
    
@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest):
    # Registrar al usuario y devolver un token
    user = register_user(data.nombre, data.apellido, data.email, data.password, data.creado_por)
    token = create_access_token({"sub": str(user.id_usuario)})
    return {"access_token": token, "token_type": "bearer"}