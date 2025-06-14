import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from typing import AsyncGenerator

# Add the project root to the path to allow imports from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.db import get_session, engine
from app.modules.users.models import Usuario, Administrador, Cliente
from app.modules.users.schemas import UsuarioCreate
from app.modules.users.services import crear_usuario
from app.core.enums import TipoUsuario
from app.modules.reservations.models import Reserva
from app.modules.billing.models import Inscripcion, DetalleInscripcion


# --- Main Session Override ---
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session


# --- Asynchronous Test Fixtures ---
@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """A client to make async requests to the app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
async def admin_token(async_client: AsyncClient) -> str:
    """Creates a full admin user and returns a valid auth token."""
    admin_email = "admin.conftest@test.com"
    admin_password = "adminpassword"
    
    for session in override_get_session():
        existing_user = session.exec(select(Usuario).where(Usuario.email == admin_email)).first()

        if not existing_user:
            admin_user_data = UsuarioCreate(
                nombre="Admin",
                apellido="Conftest",
                email=admin_email,
                password=admin_password,
                tipo=TipoUsuario.Administrador
            )
            new_user = crear_usuario(session, admin_user_data)
            session.refresh(new_user)
            
            admin_record = Administrador(id_usuario=new_user.id_usuario)
            session.add(admin_record)
            session.commit()

        response = await async_client.post("/api/auth/login", json={
            "email": admin_email,
            "password": admin_password
        })
        assert response.status_code == 200, f"Admin login failed in fixture: {response.text}"
        token = response.json()["access_token"]
        return token 


# --- Synchronous Test Fixtures (for legacy tests) ---
@pytest.fixture(name="session_test")
def session_fixture():
    """Provides a session for synchronous tests."""
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session_test: Session):
    """Provides a synchronous TestClient."""
    def get_session_override_sync():
        yield session_test
    
    app.dependency_overrides[get_session] = get_session_override_sync
    with TestClient(app) as c:
        yield c
    # Restore the main override
    app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="function")
def test_user_token(client: TestClient, session_test: Session) -> str:
    """Creates a standard client user, handling cleanup, and returns an auth token."""
    test_user_data = {
        "nombre": "Test", "apellido": "User", "email": "jitojif852@adrewire.com",
        "password": "testpassword", "tipo_documento": "DNI", "num_doc": "12345678",
        "numero_telefono": "987654321", "id_departamento": 14, "id_distrito": 1,
        "talla": 170, "peso": 70
    }
    
    # Comprehensive cleanup logic from the old conftest
    existing_cliente = session_test.exec(select(Cliente).where(Cliente.num_doc == test_user_data["num_doc"])).first()
    if existing_cliente:
        reservas = session_test.exec(select(Reserva).where(Reserva.id_cliente == existing_cliente.id_cliente)).all()
        for r in reservas: session_test.delete(r)
        
        inscripciones = session_test.exec(select(Inscripcion).where(Inscripcion.id_cliente == existing_cliente.id_cliente)).all()
        for i in inscripciones:
             detalles = session_test.exec(select(DetalleInscripcion).where(DetalleInscripcion.id_inscripcion == i.id_inscripcion)).all()
             for d in detalles: session_test.delete(d)
             session_test.delete(i)

        user_to_delete = session_test.get(Usuario, existing_cliente.id_usuario)
        session_test.delete(existing_cliente)
        if user_to_delete: session_test.delete(user_to_delete)
        session_test.commit()

    # Create user via API
    response = client.post("/api/usuarios/cliente", json=test_user_data)
    assert response.status_code == 200, f"Failed to create client: {response.text}"

    # Activate user directly in DB
    user_db = session_test.exec(select(Usuario).where(Usuario.email == test_user_data["email"])).first()
    assert user_db, "User not found after creation"
    user_db.estado = True
    session_test.add(user_db)
    session_test.commit()

    # Login to get token
    login_data = {"email": test_user_data["email"], "password": test_user_data["password"]}
    token_response = client.post("/api/auth/login", json=login_data)
    assert token_response.status_code == 200, f"Failed to get token: {token_response.text}"
    return token_response.json()["access_token"] 