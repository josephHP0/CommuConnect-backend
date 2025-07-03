import pytest
import json
from httpx import AsyncClient, ASGITransport
from app.main import app

# --- Datos para login ---
LOGIN_DATA = {
    "email": "cr@cc.com",  # ⚠️ Asegúrate de que este usuario existe y tiene la reserva
    "password": "1234"
}

# --- Helper para obtener token real ---
async def _get_auth_headers(client: AsyncClient) -> dict:
    resp = await client.post("/api/auth/login", json=LOGIN_DATA)
    assert resp.status_code == 200, f"Login falló: {resp.status_code}"
    token = resp.json().get("access_token")
    assert token, "No se devolvió access_token"
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_resumen_virtual_exitoso():
    transport = ASGITransport(app=app, raise_app_exceptions=True)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = await _get_auth_headers(client)

        id_reserva = 108  # ⚠️ Asegúrate que esta reserva sea virtual y pertenezca al usuario logueado

        response = await client.get(
            f"/api/reservations/virtual/summary/reserva/{id_reserva}",
            headers=headers
        )

        assert response.status_code == 200, f"Falló con {response.status_code}"

        data = response.json()

        print("\n🔎 JSON de respuesta (resumen de reserva virtual):")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        assert data["id_sesion"] == 2  # ⚠️ Ajusta si cambia
        assert data["link_formulario"].startswith("http")
        assert isinstance(data["nombres"], str) and data["nombres"]
        assert isinstance(data["apellidos"], str) and data["apellidos"]
        assert "mensaje_exito" in data
        assert "nota" in data
