import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Login exitoso
def test_login_exitoso():
    response = client.post("/api/auth/login", json={
        "email": "carlos.lopez@demo.com",
        "password": "Segura123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

# 2. Login con contraseña incorrecta
def test_login_contraseña_incorrecta():
    response = client.post("/api/auth/login", json={
        "email": "carlos.lopez@demo.com",
        "password": "ContraseñaIncorrecta123"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"

# 3. Login con usuario que no existe
def test_login_usuario_inexistente():
    response = client.post("/api/auth/login", json={
        "email": "noexiste@demo.com",
        "password": "AlgunaClave123"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"
