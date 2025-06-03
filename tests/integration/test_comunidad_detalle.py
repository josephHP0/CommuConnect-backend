import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Agregar raíz del proyecto al path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

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

def test_obtener_comunidad_detalle(auth_headers):
    id_comunidad = 8  # Usa un ID de comunidad activo y existente

    response = client.get(f"/api/usuarios/usuario/comunidad/{id_comunidad}", headers=auth_headers)
    
    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()

    print("\n✅ Respuesta del endpoint /usuario/comunidad/{id_comunidad}:")
    print(json.dumps(data, indent=2))

    # Validaciones básicas
    assert "id_comunidad" in data
    assert "nombre" in data
    assert "slogan" in data  # Ahora verificamos slogan en lugar de descripcion
    assert "imagen" in data
    assert "servicios" in data
    assert isinstance(data["servicios"], list)

    if data["servicios"]:
        primer_servicio = data["servicios"][0]
        assert "id_servicio" in primer_servicio
        assert "nombre" in primer_servicio
        assert "descripcion" in primer_servicio
        assert "imagen" in primer_servicio
