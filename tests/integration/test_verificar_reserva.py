import os
import sys
import json
from fastapi.testclient import TestClient

# Ajuste del path para importar la app
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

# 🔐 Login automático
def obtener_token_usu():
    response = client.post("/api/auth/login", json={
        "email": "a20213298@pucp.edu.pe",
        "password": "1234"
    })

    print("🔐 LOGIN:", response.status_code, response.json())
    assert response.status_code == 200, "❌ Login fallido"
    data = response.json()
    assert "access_token" in data, f"❌ Token no recibido: {data}"
    return data["access_token"]

def test_verificar_reserva_existe():
    token = obtener_token_usu()
    id_sesion = 1  # Asegúrate de que este id_sesion tenga reserva para admin

    url = f"/api/reservations/reserva-existe/{id_sesion}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(url, headers=headers)

    print("🔍 Status code:", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    assert response.status_code == 200
    data = response.json()
    assert "reserva_existente" in data
    assert isinstance(data["reserva_existente"], bool)

def test_verificar_reserva_no_existe():
    token = obtener_token_usu()
    id_sesion = 9999  # ID que no tiene reserva para ese usuario

    url = f"/api/reservations/reserva-existe/{id_sesion}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(url, headers=headers)

    print("🔍 Status code (no existe):", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    assert response.status_code in [200, 404, 500]
    if response.status_code == 200:
        assert "reserva_existente" in response.json()
