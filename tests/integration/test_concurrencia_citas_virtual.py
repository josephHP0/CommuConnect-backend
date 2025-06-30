# tests/integration/test_reservas_virtuales.py

import sys
import os
import threading

from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select
from app.main import app
from app.core.db import engine
from app.modules.reservations.models import Reserva
from app.modules.users.models import Usuario
from app.modules.users.models import Cliente  

# 1) Aseguramos que la raíz del proyecto esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2) Creamos el TestClient global (aunque cada hilo creará el suyo)
client = TestClient(app)

# Credenciales de usuario A y usuario B
LOGIN_DATA_A = {"email": "pm@cc.com", "password": "1234"}
LOGIN_DATA_B = {"email": "lr@cc.com", "password": "1234"}

# Comunidad válida compartida entre ambos usuarios
ID_COMUNIDAD = 1  # Ambos usuarios deben estar inscritos en esta comunidad

def _get_auth_headers(login_data):
    resp = client.post("/api/auth/login", json=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_concurrent_reserva_virtual_dos_usuarios(crear_sesion_virtual):
    """
    Verifica que, al lanzar dos reservas virtuales en paralelo
    con usuarios distintos, solo una reciba 201 y la otra 409.
    """
    # La sesión creada por la fixture
    id_sesion = crear_sesion_virtual.id_sesion

    # Payload común
    payload = {"id_sesion": id_sesion, "id_comunidad": ID_COMUNIDAD}

    # Autenticamos cada usuario y obtenemos sus cabeceras
    headers_a = _get_auth_headers(LOGIN_DATA_A)
    headers_b = _get_auth_headers(LOGIN_DATA_B)

    # --- Limpiamos reservas previas para ambos clientes en esta comunidad ---
    with Session(engine) as db:
        # Buscar id_cliente de cada usuario
        user_a = db.exec(select(Usuario).where(Usuario.email == LOGIN_DATA_A["email"])).one()
        client_a = db.exec(select(Cliente).where(Cliente.id_usuario == user_a.id_usuario)).one()
        user_b = db.exec(select(Usuario).where(Usuario.email == LOGIN_DATA_B["email"])).one()
        client_b = db.exec(select(Cliente).where(Cliente.id_usuario == user_b.id_usuario)).one()

        # Borramos todas las reservas de esos dos clientes en la comunidad
        db.exec(
            delete(Reserva).where(
                Reserva.id_comunidad == ID_COMUNIDAD,
                Reserva.id_cliente.in_([client_a.id_cliente, client_b.id_cliente])
            )
        )
        db.commit()

    # Arrays para capturar resultados de los threads
    results = [None, None]
    responses = [None, None]

    def intentar_reserva(idx, headers):
        # Cada hilo crea su propio cliente para el app
        local_client = TestClient(app)
        resp = local_client.post("/api/reservations/virtual", json=payload, headers=headers)
        results[idx] = resp.status_code
        responses[idx] = resp.json()

    # Lanzamos en paralelo
    h1 = threading.Thread(target=intentar_reserva, args=(0, headers_a))
    h2 = threading.Thread(target=intentar_reserva, args=(1, headers_b))
    h1.start()
    h2.start()
    h1.join()
    h2.join()

    # Solo debe haber una 201 y una 409
    assert results.count(201) == 1, f"Esperaba una sola 201, got {results} – {responses}"
    assert results.count(409) == 1, f"Esperaba una sola 409, got {results} – {responses}"