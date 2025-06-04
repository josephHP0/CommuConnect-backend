from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.modules.users.models import Usuario
from app.modules.auth.schemas import LoginRequest, TokenResponse, RegisterRequest
from app.core.security import verify_password, create_access_token
from app.core.db import engine  # o como tengas tu conexión
from app.modules.services.services import register_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(Usuario).where(Usuario.email == data.email)).first()
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = create_access_token(str(user.id_usuario))
        return {"access_token": token,"user_rol": user.tipo.value}
