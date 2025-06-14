# tests/integration/test_reservas_virtuales.py
import sys
import os
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlmodel import Session
from app.modules.reservations.models import Reserva
from sqlmodel import delete


# 1) Configura el entorno del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2) Importa la app y recursos
from app.main import app
from app.core.db import engine
from app.modules.reservations.models import Sesion
client = TestClient(app)

# 3) Credenciales válidas para un usuario existente
LOGIN_DATA = {
    "email": "lr@cc.com",
    "password": "1234"
}

# 4) Función de login para obtener token
def _get_auth_headers():
    resp = client.post("/api/auth/login", json=LOGIN_DATA)
    assert resp.status_code == 200, f"Login falló: {resp.status_code}"
    token = resp.json().get("access_token")
    assert token, "No se devolvió access_token"
    return {"Authorization": f"Bearer {token}"}

# 5) Fixture: crea una sesión virtual nueva y retorna su ID
@pytest.fixture
def crear_sesion_virtual():
    now = datetime.utcnow()
    nueva_sesion = Sesion(
        inicio=now + timedelta(days=1),
        fin=now + timedelta(days=1, hours=1),
        tipo="Virtual",
        id_servicio=1,  # Asegúrate que este ID de servicio exista
        descripcion="Sesión de prueba para test"
    )

    with Session(engine) as db:
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        return nueva_sesion

def test_create_reserva_virtual_conflict(crear_sesion_virtual):
    headers = _get_auth_headers()
    payload = {"id_sesion": crear_sesion_virtual.id_sesion}

    # 1) Elimina cualquier reserva existente para ese cliente y sesión
    with Session(engine) as db:
        db.exec(delete(Reserva).where(
            Reserva.id_sesion == crear_sesion_virtual.id_sesion,
            Reserva.id_cliente == 13 
        ))
        db.commit()

    # 2) Primera reserva → debería ser exitosa
    resp1 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("Primera reserva:", resp1.status_code, resp1.json())
    assert resp1.status_code == 201

    # 3) Segunda reserva sobre la misma sesión → debe ser 409
    resp2 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("Segunda reserva:", resp2.status_code, resp2.json())
    assert resp2.status_code == 409

# 7) Test: conflicto por reserva duplicada
def test_create_reserva_virtual_conflict(crear_sesion_virtual):
    headers = _get_auth_headers()
    payload = {"id_sesion": crear_sesion_virtual.id_sesion}

    # Primera reserva → OK
    resp1 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Segunda reserva → debe fallar
    resp2 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    assert resp2.status_code == 409, f"Esperaba 409, got {resp2.status_code}\n{resp2.text}"

# 8) Test: sesión no existente
def test_create_reserva_virtual_not_found():
    headers = _get_auth_headers()
    payload = {"id_sesion": 999999}  # ID ficticio que no existe

    response = client.post("/api/reservations/virtual", json=payload, headers=headers)
    assert response.status_code == 404, f"Esperaba 404, got {response.status_code}\n{response.text}"
