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
    "email": "lr@cc.com",  # Asegúrate de que tiene una inscripción activa / si tiene: mr@cc.com
    "password": "1234"
}
@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Error login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_validar_membresia_en_comunidad(auth_headers):
    id_comunidad = 1  # Confirmado que el cliente ID=103 tiene membresía activa en esta comunidad

    response = client.get(
        f"/api/billing/usuario/validar-membresia/{id_comunidad}",
        headers=auth_headers
    )

    assert response.status_code == 200, f"Error HTTP: {response.text}"
    
    data = response.json()
    print("\nRespuesta del endpoint /usuario/validar-membresia/{id_comunidad}:")
    print(json.dumps(data, indent=2))

    # Validación estricta
    assert "tieneMembresiaActiva" in data
    assert isinstance(data["tieneMembresiaActiva"], bool)
    
