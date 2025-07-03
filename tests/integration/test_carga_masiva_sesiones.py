import os
import pytest
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ⚙️ Datos de login de un admin ya registrado
LOGIN_DATA = {
    "email": "bernardo@pucp.com",
    "password": "1234"
}

# ✅ Fixture para autenticación con JWT
@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"❌ Error en login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ✅ Test de carga masiva
def test_carga_masiva_sesiones_virtuales(auth_headers):
    ruta_archivo = r"C:\Users\berna\ProyectosGitHub\sesiones_virtuales_demo.xlsx"

    # Verificar que el archivo de prueba existe
    assert os.path.exists(ruta_archivo), f"❌ No se encontró el archivo: {ruta_archivo}"

    # Enviar archivo al endpoint
    with open(ruta_archivo, "rb") as f:
        response: Response = client.post(
            "/api/reservations/carga-masiva",  # ✅ Revisa que esta ruta coincida con tu router
            files={
                "archivo": (
                    "sesiones_virtuales_demo.xlsx",
                    f,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            },
            headers=auth_headers
        )
    # 👉 Intenta obtener siempre el JSON (aunque haya fallado)
    try:
        data = response.json()
    except Exception:
        data = {"error": "No se pudo decodificar JSON", "raw": response.text}

    print("\n📦 JSON de respuesta:")
    print(data)

    # Validar respuesta
    assert response.status_code == 200, f"❌ Error HTTP: {response.status_code} - {response.text}"
    data = response.json()
    assert "mensaje" in data
    assert "resumen" in data
    print("✅ Test de carga masiva exitoso.")
