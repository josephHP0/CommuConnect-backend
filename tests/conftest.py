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
    """
    Provides a session for synchronous tests. It ensures a clean state
    by cleaning the test user and then commits the transaction.
    """
    # Safeguard: directly clean up the test user if it exists
    with Session(engine) as cleanup_session:
        existing_user = cleanup_session.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).first()
        if existing_user:
            existing_cliente = cleanup_session.exec(select(Cliente).where(Cliente.id_usuario == existing_user.id_usuario)).first()
            if existing_cliente:
                # This needs to be more thorough to avoid foreign key issues
                reservas = cleanup_session.exec(select(Reserva).where(Reserva.id_cliente == existing_cliente.id_cliente)).all()
                for r in reservas: cleanup_session.delete(r)
                
                inscripciones = cleanup_session.exec(select(Inscripcion).where(Inscripcion.id_cliente == existing_cliente.id_cliente)).all()
                for i in inscripciones:
                    detalles = cleanup_session.exec(select(DetalleInscripcion).where(DetalleInscripcion.id_inscripcion == i.id_inscripcion)).all()
                    for d in detalles: cleanup_session.delete(d)
                    cleanup_session.delete(i)
                
                cleanup_session.delete(existing_cliente)
            cleanup_session.delete(existing_user)
        cleanup_session.commit()

    with Session(engine) as session:
        yield session
        session.commit() # Commit changes made during the test

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
    """
    Creates a standard client user directly in the DB using the transactional session,
    activates it, and returns an auth token. This is the most robust way.
    """
    # 1. Create user directly in the transactional session
    user_email = "jitojif852@adrewire.com"
    user_password = "testpassword"

    usuario_data = UsuarioCreate(
        nombre="Test",
        apellido="User",
        email=user_email,
        password=user_password,
        tipo=TipoUsuario.Cliente
    )
    new_user = crear_usuario(db=session_test, usuario=usuario_data)
    new_user.estado = True # Activate user
    
    cliente_data = Cliente(
        id_usuario=new_user.id_usuario,
        tipo_documento="DNI",
        num_doc="12345678",
        numero_telefono="987654321",
        id_departamento=14,
        id_distrito=1,
        talla=170,
        peso=70
    )
    session_test.add_all([new_user, cliente_data])
    session_test.commit()

    # 2. Login via API to get token
    login_data = {"email": user_email, "password": user_password}
    token_response = client.post("/api/auth/login", json=login_data)
    assert token_response.status_code == 200, f"Failed to get token for test user: {token_response.text}"
    return token_response.json()["access_token"] 