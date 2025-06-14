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

# 2) Creamos el TestClient global (aunque cada hilo creará el suyo)
client = TestClient(app)

# Credenciales de usuario A y usuario B
LOGIN_DATA_A = {"email": "ms@cc.com", "password": "1234"}
LOGIN_DATA_B = {"email": "lr@cc.com", "password": "1234"}

# Comunidad válida compartida entre ambos usuarios
ID_COMUNIDAD = 1  #Asegúrate que ambos usuarios estén inscritos en esta comunidad
ID_SESION_VIRTUAL = 1  # Asegúrate que esta sesión virtual pertenece a la comunidad

def _get_auth_headers(login_data):
    resp = client.post("/api/auth/login", json=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_concurrent_reserva_virtual_dos_usuarios():
    payload = {
        "id_sesion": ID_SESION_VIRTUAL,
        "id_comunidad": ID_COMUNIDAD
    }

    # 1) Autenticamos cada usuario
    headers_a = _get_auth_headers(LOGIN_DATA_A)
    headers_b = _get_auth_headers(LOGIN_DATA_B)

    results = [None, None]
    responses = [None, None]

    def intentar_reserva(idx, headers):
        # Cada hilo usa su propio TestClient para evitar conflictos
        local_client = TestClient(app)
        resp = local_client.post("/api/reservations/virtual", json=payload, headers=headers)
        results[idx] = resp.status_code
        responses[idx] = resp.json()

    # 2) Creamos dos hilos, uno por usuario
    h1 = threading.Thread(target=intentar_reserva, args=(0, headers_a))
    h2 = threading.Thread(target=intentar_reserva, args=(1, headers_b))

    # 3) Ejecutamos concurrentemente
    h1.start()
    h2.start()
    h1.join()
    h2.join()

    # 4) Validación: solo uno debe obtener 201 (creado), el otro 409 (conflicto)
    assert results.count(201) == 1, f"Esperaba una sola 201, got {results} – {responses}"
    assert results.count(409) == 1, f"Esperaba una sola 409, got {results} – {responses}"
