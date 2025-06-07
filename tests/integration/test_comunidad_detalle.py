import os, sys, json, pytest
from fastapi.testclient import TestClient

# Apunta al root de tu proyecto (2 niveles arriba)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

LOGIN_DATA = {"email": "mr@cc.com", "password": "1234"}

@pytest.fixture
def auth_headers():
    resp = client.post("/api/auth/login", json=LOGIN_DATA)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_obtener_comunidad_detalle(auth_headers):
    # Usa un id válido de tu BD
    id_comunidad = 3
    url = f"/api/usuarios/usuario/comunidad/{id_comunidad}"



    resp = client.get(url, headers=auth_headers)
    print("🔍 Status code:", resp.status_code)
    print("🧾 Respuesta JSON:\n", json.dumps(resp.json(), indent=2))

    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Comprueba que vienen los campos esperados
    assert data["id_comunidad"] == id_comunidad
    assert "nombre" in data and isinstance(data["nombre"], str)
    assert "servicios" in data and isinstance(data["servicios"], list)

    # Si quieres validar los servicios uno a uno:
    for s in data["servicios"]:
        assert "nombre" in s
        assert "modalidad" in s
        # ¡Y cualquier otro campo que devuelvas!
