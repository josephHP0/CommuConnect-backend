import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
# 1. Registro exitoso de usuario
def test_registro_usuario_exitoso():
    payload = {
        "nombre": "Carlos",
        "apellido": "López",
        "email": "carlos.lopez@demo.com",
        "tipo": "CLIENTE",
        "password": "Segura123"
    }
    response = client.post("/api/usuarios/usuario", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == payload["email"]

# 2. Rechazo por email duplicado
def test_registro_usuario_email_duplicado():
    payload = {
        "nombre": "NuevoNombre",
        "apellido": "NuevoApellido",
        "email": "carlos.lopez@demo.com",
        "tipo": "CLIENTE",
        "password": "Clave123"
    }
    response = client.post("/api/usuarios/usuario", json=payload)
    assert response.status_code in (400, 409)
    assert "ya está registrado" in response.json()["detail"].lower()

# 3. Rechazo por nombre duplicado (solo si se valida como único)
def test_registro_usuario_nombre_duplicado():
    payload = {
        "nombre": "Carlos",
        "apellido": "OtroApellido",
        "email": "carlos.duplicado@demo.com",
        "tipo": "CLIENTE",
        "password": "NuevaClave456"
    }
    response = client.post("/api/usuarios/usuario", json=payload)
    assert response.status_code in (201, 400, 409)
