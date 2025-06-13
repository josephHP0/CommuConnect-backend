# tests/integration/test_reservas_virtuales.py

import sys
import os
import threading

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.main import app
from app.modules.reservations.models import Reserva

# 1) Aseguramos que la raíz del proyecto esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2) Creamos el TestClient global (cada hilo también creará el suyo)
client = TestClient(app)

# Credenciales de usuario A y usuario B
LOGIN_DATA_A = {"email": "mr@cc.com", "password": "1234"}
LOGIN_DATA_B = {"email": "lr@cc.com", "password": "1234"}

def _get_auth_headers(login_data):
    resp = client.post("/api/auth/login", json=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_concurrent_reserva_virtual_dos_usuarios():

    payload = {"id_sesion": 1}

    # 1) Autenticamos cada usuario
    headers_a = _get_auth_headers(LOGIN_DATA_A)
    headers_b = _get_auth_headers(LOGIN_DATA_B)

    results = [None, None]

    def intentar_reserva(idx, headers):
        # Cada hilo usa su propio TestClient
        local_client = TestClient(app)
        resp = local_client.post("/api/reservations/virtual", json=payload, headers=headers)
        results[idx] = resp.status_code

    # 2) Creamos dos hilos, uno para cada usuario
    h1 = threading.Thread(target=intentar_reserva, args=(0, headers_a))
    h2 = threading.Thread(target=intentar_reserva, args=(1, headers_b))

    # 3) Ejecutamos “a la vez”
    h1.start()
    h2.start()
    h1.join()
    h2.join()

    # 4) Comprobamos que solo uno obtenga 201 y el otro 409
    assert results.count(201) == 1, f"Esperaba una sola 201, got {results}"
    assert results.count(409) == 1, f"Esperaba una sola 409, got {results}"
