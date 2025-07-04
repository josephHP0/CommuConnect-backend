import sys
import os
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# Configura entorno
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importa app y recursos
from app.main import app
from app.core.db import engine
from app.modules.reservations.models import Reserva
from app.modules.billing.models import DetalleInscripcion
from app.modules.billing.models import Inscripcion

client = TestClient(app)

# 👤 Credenciales del cliente de prueba (id_usuario=42, id_cliente=103)
LOGIN_DATA = {
    "email": "gianfranco.mpc@gmail.com",
    "password": "1234"
}

# 🔐 Login helper
def _get_auth_headers():
    resp = client.post("/api/auth/login", json=LOGIN_DATA)
    assert resp.status_code == 200, f"Login falló: {resp.status_code}"
    token = resp.json().get("access_token")
    assert token, "No se devolvió access_token"
    print(f"[TOKEN RECIBIDO]: {token}")
    return {"Authorization": f"Bearer {token}"}

# 📊 Función auxiliar para consultar topes
def _get_topes(cliente_id: int, comunidad_id: int):
    with Session(engine) as db:
        inscripcion = db.exec(
            select(Inscripcion).where(
                Inscripcion.id_cliente == cliente_id,
                Inscripcion.id_comunidad == comunidad_id,
                Inscripcion.estado == 1
            )
        ).one_or_none()
        if not inscripcion:
            print("⚠️ No se encontró inscripción activa")
            return None

        detalle = db.exec(
            select(DetalleInscripcion).where(
                DetalleInscripcion.id_inscripcion == inscripcion.id_inscripcion
            )
        ).one_or_none()
        if not detalle:
            print("⚠️ No se encontró detalle de inscripción")
            return None

        return detalle.topes_disponibles, detalle.topes_consumidos

# 🧪 Test principal: reserva válida y conflicto por duplicidad
def test_reserva_virtual_conflicto():
    print("\n🧪 Iniciando test_reserva_virtual_conflicto...")

    headers = _get_auth_headers()

    payload = {
        "id_sesion": 310,     # Sesión virtual real, de la comunidad 1 (Runners_LAB6)
        "id_comunidad": 1
    }

    id_cliente = 103
    id_inscripcion = 54  # Asociada a comunidad 1

    print(f"📦 Payload preparado: {payload}")

    with Session(engine) as db:
        # Verifica si ya hay reservas
        reservas_previas = db.exec(
            select(Reserva).where(
                Reserva.id_sesion == payload["id_sesion"],
                Reserva.id_cliente == id_cliente
            )
        ).all()
        print(f"📊 Reservas previas en sesión {payload['id_sesion']} → {len(reservas_previas)}")

        # Verifica topes antes de reservar
        topes_antes = _get_topes(id_cliente, payload["id_comunidad"])
        if topes_antes:
            print(f"📉 Topes antes: disponibles={topes_antes[0]}, consumidos={topes_antes[1]}")

    # Primera reserva (debe pasar)
    resp1 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("✅ Primera reserva:")
    print("   Código:", resp1.status_code)
    print("   JSON:", resp1.json())
    assert resp1.status_code == 201

    # Segunda reserva (debe fallar por duplicado)
    resp2 = client.post("/api/reservations/virtual", json=payload, headers=headers)
    print("🚫 Segunda reserva (esperado conflicto):")
    print("   Código:", resp2.status_code)
    print("   JSON:", resp2.json())
    assert resp2.status_code == 409

    # Verifica topes después de reservar
    topes_despues = _get_topes(id_cliente, payload["id_comunidad"])
    if topes_despues:
        print(f"📈 Topes después: disponibles={topes_despues[0]}, consumidos={topes_despues[1]}")
