from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.modules.auth.dependencies import get_current_cliente_id, get_current_user
from app.modules.communities.models import ClienteXComunidad
from app.modules.users.models import Usuario
from app.modules.auth.schemas import CambioPasswordIn, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.db import engine, get_session
from app.modules.auth.services import pwd_context, hash_password

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

@router.post("/usuario/cambiar-password")
def cambiar_password(
    datos: CambioPasswordIn,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    # Verifica contraseña actual
    if not pwd_context.verify(datos.actual, current_user.password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    # Verifica que las nuevas coincidan
    if datos.nueva != datos.repetir:
        raise HTTPException(status_code=400, detail="Las contraseñas nuevas no coinciden")
    # Opcional: puedes agregar validaciones de seguridad para la nueva contraseña aquí

    # Cambia la contraseña
    current_user.password = hash_password(datos.nueva)
    current_user.fecha_modificacion = datetime.utcnow()
    session.add(current_user)
    session.commit()
    return {"ok": True, "message": "Contraseña cambiada exitosamente"}
