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

# Credenciales válidas de un cliente cuyo id_cliente = 17 (usuario mr@cc.com)
LOGIN_DATA = {
    "email": "mr@cc.com",
    "password": "1234"
}

@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Error login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_obtener_uso_topes_cliente17(auth_headers):
    id_comunidad = 4  # Confirmado que el cliente tiene inscripción activa

    response = client.get(f"/api/usuarios/usuario/comunidad/{id_comunidad}/topes", headers=auth_headers)
    
    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()

    print("\nRespuesta del endpoint /usuario/comunidad/{id_comunidad}/topes:")
    print(json.dumps(data, indent=2))

    # Validaciones dinámicas mínimas
    assert "estado" in data
    assert "plan" in data
    if data["plan"] == "Plan por Topes":
        assert "topes_disponibles" in data
        assert "topes_consumidos" in data
