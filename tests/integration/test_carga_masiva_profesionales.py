import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

LOGIN_DATA = {
    "email": "bernardo@pucp.com",
    "password": "1234"
}

@pytest.fixture
def auth_headers():
    response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200, f"Error en login: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_carga_masiva_profesionales(auth_headers):
    ruta_archivo = r"C:\Users\berna\ProyectosGitHub\profesionales_demo.xlsx"
    assert os.path.exists(ruta_archivo), "⚠️ No se encontró el archivo de prueba"

    with open(ruta_archivo, "rb") as f:
        response = client.post(
            "/api/services/carga-masiva",
            files={"archivo": ("profesionales_demo.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=auth_headers
        )

    assert response.status_code == 200, f"Error HTTP: {response.text}"
    data = response.json()
    print("\nRespuesta del endpoint /api/services/carga-masiva:")
    print(data)

    assert "resumen" in data
    assert "insertados" in data["resumen"]
    assert data["resumen"]["insertados"] > 0
