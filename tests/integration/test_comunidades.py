import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os
from typing import AsyncGenerator

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.main import app
from app.core.db import get_session, engine
from app.modules.users.models import Usuario, Administrador
from app.modules.users.schemas import UsuarioCreate
from app.modules.users.services import crear_usuario
from app.core.enums import TipoUsuario
from sqlmodel import Session, select

# Override the app's session dependency
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
async def admin_token(async_client: AsyncClient) -> str:
    admin_email = "admin.comunidades.final.test@test.com"
    admin_password = "adminpassword"
    
    for session in app.dependency_overrides[get_session]():
        existing_user = session.exec(select(Usuario).where(Usuario.email == admin_email)).first()

        if not existing_user:
            admin_user_data = UsuarioCreate(
                nombre="AdminFinal",
                apellido="Test",
                email=admin_email,
                password=admin_password,
                tipo=TipoUsuario.Administrador
            )
            new_user = crear_usuario(session, admin_user_data)
            session.refresh(new_user)
            
            admin_record = Administrador(id_usuario=new_user.id_usuario)
            session.add(admin_record)
            session.commit()
            session.refresh(new_user)
            session.refresh(admin_record)

        response = await async_client.post("/api/auth/login", json={
            "email": admin_email,
            "password": admin_password
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return token

@pytest.mark.asyncio
async def test_crear_comunidad_con_imagen(admin_token: str, async_client: AsyncClient):
    community_data = {
        "nombre": "Comunidad Async Test con Imagen",
        "slogan": "Slogan async de prueba con imagen",
    }

    with open("./tests/integration/assets/test_image.png", "rb") as f:
        files = {"imagen": ("test_image.png", f, "image/png")}
        response = await async_client.post(
            "/api/comunidades/crear_comunidad",
            data=community_data,
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    assert response.status_code == 200, response.text

@pytest.mark.asyncio
async def test_crear_comunidad_sin_imagen(admin_token: str, async_client: AsyncClient):
    community_data = {
        "nombre": "Comunidad Async Test sin Imagen",
        "slogan": "Slogan async de prueba sin imagen",
    }

    response = await async_client.post(
        "/api/comunidades/crear_comunidad",
        data=community_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200, response.text
