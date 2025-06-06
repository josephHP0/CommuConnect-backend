from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from app.modules.communities.models import ClienteXComunidad
from app.modules.users.models import Usuario
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.core.db import engine, get_session
from app.modules.services.services import register_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(Usuario).where(Usuario.email == data.email)).first()
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = create_access_token(str(user.id_usuario))
        return {"access_token": token,"user_rol": user.tipo.value} # type: ignore
    
@router.get("/tiene-comunidades")
def tiene_comunidades(
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id)
):
    existe = session.exec(
        select(ClienteXComunidad).where(ClienteXComunidad.id_cliente == id_cliente)
    ).first()
    return {"tiene_comunidades": existe is not None}
