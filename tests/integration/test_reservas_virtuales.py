# tests/integration/test_reservas_virtuales.py

import sys
import os
from fastapi.testclient import TestClient

# 1) Aseguramos que la raíz del proyecto esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2) Importamos la app y creamos el TestClient
from app.main import app
client = TestClient(app)

# 3) Credenciales de un usuario existente
LOGIN_DATA = {
    "email": "mr@cc.com",
    "password": "1234"
}

def _get_auth_headers():
    resp = client.post("/api/auth/login", json=LOGIN_DATA)
    assert resp.status_code == 200, f"Login falló: {resp.status_code}"
    token = resp.json().get("access_token")
    assert token, "No se devolvió access_token"
    return {"Authorization": f"Bearer {token}"}

def test_create_reserva_virtual_success():
    headers = _get_auth_headers()
    payload = {"id_sesion": 1}

    response = client.post(
        "/api/reservations/virtual",
        json=payload,
        headers=headers
    )

    # Imprime el JSON que devuelve el endpoint
    print("RESPONSE JSON (success):", response.json())

    # Ahora los asserts habituales
    assert response.status_code == 201, f"Esperaba 201, got {response.status_code}\n{response.text}"
    data = response.json()
    assert data["id_sesion"] == payload["id_sesion"]
    assert "id_reserva" in data


def test_create_reserva_virtual_conflict():
    headers = _get_auth_headers()
    payload = {"id_sesion": 1}

    # Primera reserva → OK
    resp1 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    assert resp1.status_code == 201
        # Imprime el JSON que te devuelve el endpoint


    # Segunda reserva sobre la misma sesión → debe ser 409 Conflict
    resp2 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    assert resp2.status_code == 409, f"Esperaba 409, got {resp2.status_code}\n{resp2.text}"


def test_create_reserva_virtual_not_found():
    headers = _get_auth_headers()
    payload = {"id_sesion": 9999}

    response = client.post(
        "/api/reservations/virtual",
        json=payload,
        headers=headers
    )
    # Sesión inexistente → 404 Not Found
    assert response.status_code == 404, f"Esperaba 404, got {response.status_code}\n{response.text}"
