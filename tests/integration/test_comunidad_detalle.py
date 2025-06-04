import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# 🧠 Forzar que app/ sea reconocida como paquete
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app  # Ahora sí debería funcionar

client = TestClient(app)
# (Opcional) Si el endpoint requiere token JWT
LOGIN_DATA = {
    "email": "lucia.ramirez@gmail.com",
    "password": "clave123"
}

@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 🧪 Prueba del endpoint distritos por servicio
def test_obtener_distritos_por_servicio():  # Puedes agregar auth_headers si lo usas
    id_servicio = 2  # Reemplaza con un ID real de tu BD
    url = f"/api/geography/usuario/servicio/{id_servicio}/distritos"

    response = client.get(url)  # Si usas autenticación: , headers=auth_headers

    print("🔍 Status code:", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2))

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert all("id_distrito" in d and "nombre" in d for d in data)
