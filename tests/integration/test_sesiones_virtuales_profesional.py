from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

LOGIN_DATA = {
    "email": "bernardo@pucp.com",
    "password": "1234"
}


def test_listar_sesiones_virtuales_de_profesionales_existente_y_noexistente():
    # Autenticarse como administrador
    login_response = client.post("/api/auth/login", json=LOGIN_DATA)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ---------- Profesional que SÍ tiene sesiones ----------
    response_existente = client.get(
        "/api/services/profesionales/1/sesiones-virtuales",
        headers=headers
    )
    print("✅ JSON profesional EXISTENTE:")
    print(response_existente.json())  # 👈 Aquí se imprime el JSON
    print("[RESPUESTA EXISTENTE]", response_existente.json())

    assert response_existente.status_code == 200
    assert isinstance(response_existente.json(), list)

    # ---------- Profesional que NO tiene sesiones ----------
    response_inexistente = client.get(
        "/api/services/profesionales/9999/sesiones-virtuales",
        headers=headers
    )
    print("SON profesional INEXISTENTE:")
    print(response_inexistente.json())  # 👈 También aquí
    print("[RESPUESTA EXISTENTE]", response_existente.json())

    assert response_inexistente.status_code == 200
    assert response_inexistente.json() == []