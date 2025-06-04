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

# Usa credenciales válidas de un cliente cuyo id_cliente = 4
LOGIN_DATA = {
    "email": "lucia.ramirez@gmail.com",
    "password": "clave123"
}
@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Error login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_obtener_uso_topes_cliente4(auth_headers):
    id_comunidad = 7  # Cliente 4 está inscrito con topes en la comunidad 7

    response = client.get(f"/api/usuarios/usuario/comunidad/{id_comunidad}/topes", headers=auth_headers)
    
    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()

    print("\nRespuesta del endpoint /usuario/comunidad/{id_comunidad}/topes:")
    print(json.dumps(data, indent=2))

    # Validaciones esperadas
    assert data["plan"] == "Plan por Topes"
    assert data["topes_disponibles"] == 15
    assert data["topes_consumidos"] == 5
    assert data["estado"] == "Restan 15 de 20"
