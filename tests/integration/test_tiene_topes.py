import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Agrega la raíz del proyecto al path para importar correctamente
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

LOGIN_DATA = {
    "email": "mr@cc.com",  # Cliente con inscripción activa en comunidad 1 y plan por topes
    "password": "1234"
}

@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Error login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_tiene_topes_cliente_con_topes(auth_headers):
    id_comunidad = 1  # Comunidad donde el cliente tiene inscripción activa con topes

    response = client.get(
        f"/api/billing/usuario/comunidad/{id_comunidad}/tiene-topes",
        headers=auth_headers
    )

    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()
    print("\n Respuesta del endpoint /tiene-topes (cliente con topes):")
    print(json.dumps(data, indent=2))

    assert "tieneTopes" in data
    assert isinstance(data["tieneTopes"], bool)
    assert data["tieneTopes"] is True  # Cambiar a False si el cliente ya no tiene topes

def test_tiene_topes_cliente_sin_inscripcion(auth_headers):
    id_comunidad = 1  # Comunidad inexistente o sin inscripción activa

    response = client.get(
        f"/api/billing/usuario/comunidad/{id_comunidad}/tiene-topes",
        headers=auth_headers
    )

    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()
    print("\nRespuesta del endpoint /tiene-topes (cliente sin inscripción):")
    print(json.dumps(data, indent=2))

    assert "tieneTopes" in data
    assert isinstance(data["tieneTopes"], bool)
    assert data["tieneTopes"] is False
