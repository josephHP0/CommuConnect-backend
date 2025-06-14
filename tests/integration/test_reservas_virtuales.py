# tests/integration/test_reservas_virtuales.py

import sys
import os
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, delete
from app.modules.reservations.models import Reserva, Sesion

# Configura entorno
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importa app y recursos
from app.main import app
from app.core.db import engine

client = TestClient(app)

# Credenciales válidas
LOGIN_DATA = {
    "email": "lr@cc.com",
    "password": "1234"
}

# Login helper
def _get_auth_headers():
    resp = client.post("/api/auth/login", json=LOGIN_DATA)
    assert resp.status_code == 200, f"Login falló: {resp.status_code}"
    token = resp.json().get("access_token")
    assert token, "No se devolvió access_token"
    return {"Authorization": f"Bearer {token}"}

# Crea sesión virtual dummy
@pytest.fixture
def crear_sesion_virtual():
    now = datetime.now(timezone.utc)
    nueva_sesion = Sesion(
        inicio=now + timedelta(days=1),
        fin=now + timedelta(days=1, hours=1),
        tipo="Virtual",
        id_servicio=1,  # ⚠️ Asegúrate que exista
        descripcion="Sesión de prueba para test"
    )
    with Session(engine) as db:
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        return nueva_sesion

# Test: no permitir doble reserva en la misma sesión virtual
def test_reserva_virtual_conflicto(crear_sesion_virtual):
    headers = _get_auth_headers()
    payload = {
        "id_sesion": crear_sesion_virtual.id_sesion,
        "id_comunidad": 1  # ⚠️ Asegúrate que el cliente esté inscrito en esta comunidad
    }

    # Elimina reservas previas del cliente 13 (asociado a lr@cc.com)
    with Session(engine) as db:
        db.exec(delete(Reserva).where(
            Reserva.id_sesion == crear_sesion_virtual.id_sesion,
            Reserva.id_cliente == 13  # ⚠️ Asegúrate que sea el ID correcto
        ))
        db.commit()

    # Primera reserva (debe pasar)
    resp1 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("Primera reserva:", resp1.status_code, resp1.json())
    assert resp1.status_code == 201

    # Segunda reserva (debe fallar por conflicto)
    resp2 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("Segunda reserva:", resp2.status_code, resp2.json())
    assert resp2.status_code == 409

# Test: sesión inexistente
def test_reserva_virtual_sesion_no_encontrada():
    headers = _get_auth_headers()
    payload = {
        "id_sesion": 999999,     # Sesión inexistente
        "id_comunidad": 1        # Comunidad válida
    }

    response = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("Reserva en sesión inexistente:", response.status_code, response.json())
    assert response.status_code == 404, f"Esperaba 404, got {response.status_code}\n{response.text}"
