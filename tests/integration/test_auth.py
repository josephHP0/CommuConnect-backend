import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi.testclient import TestClient
from app.main import app
from app.modules.users.schemas import UsuarioCreate
from app.modules.users.services import crear_usuario
from app.core.db import Session, get_session

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_auth_users(session_test: Session):
    """Crea usuarios necesarios para las pruebas de autenticación."""
    users_to_create = [
        UsuarioCreate(email="auth.test@example.com", password="SecurePassword123", nombre="AuthUser", apellido="Test", tipo="CLIENTE"),
    ]
    for user_data in users_to_create:
        # Evita errores si el usuario ya existe por una ejecución anterior
        from sqlmodel import select
        from app.modules.users.models import Usuario
        existing_user = session_test.exec(select(Usuario).where(Usuario.email == user_data.email)).first()
        if not existing_user:
            crear_usuario(session_test, user_data)
            session_test.commit()

# 1. Login exitoso
def test_login_exitoso():
    response = client.post("/api/auth/login", json={
        "email": "auth.test@example.com",
        "password": "SecurePassword123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

# 2. Login con contraseña incorrecta
def test_login_contraseña_incorrecta():
    response = client.post("/api/auth/login", json={
        "email": "auth.test@example.com",
        "password": "WrongPassword"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"

# 3. Login con usuario que no existe
def test_login_usuario_inexistente():
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@user.com",
        "password": "AnyPassword"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"
