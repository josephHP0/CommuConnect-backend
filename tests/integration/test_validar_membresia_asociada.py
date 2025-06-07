# tests/integration/test_validar_membresia_asociada.py

import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Agrega la raíz del proyecto al path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

# Credenciales válidas
LOGIN_DATA = {
    "email": "cr@cc.com",  # Asegúrate de que tiene una inscripción activa / si tiene: mr@cc.com
    "password": "1234"
}


@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Error login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_validar_membresia_asociada(auth_headers):
    response = client.get("/api/billing/usuario/validar-membresia-asociada", headers=auth_headers)

    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()
    print("\nRespuesta del endpoint /api/billing/usuario/validar-membresia-asociada:")
    print(json.dumps(data, indent=2))

    assert "tieneMembresiaAsociada" in data, "Falta la clave 'tieneMembresiaAsociada'"
    assert isinstance(data["tieneMembresiaAsociada"], bool), "'tieneMembresiaAsociada' debe ser booleano"
