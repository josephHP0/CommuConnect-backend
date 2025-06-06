import os
import sys
import json
from fastapi.testclient import TestClient

# Ajuste del path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

def test_get_fechas_sesiones_existente():
    id_profesional = 1  # Asegúrate que este ID tenga sesiones virtuales en tu base de datos

    url = f"/api/reservations/fechas-sesiones_virtuales_por_profesional/{id_profesional}"
    response = client.get(url)

    print("🔍 Status code:", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    assert response.status_code == 200
    data = response.json()

    assert "fechas_inicio" in data
    assert isinstance(data["fechas_inicio"], list)

def test_get_fechas_sesiones_no_existe():
    id_profesional = 9999  # ID que no tenga sesiones virtuales asociadas

    url = f"/api/reservations/fechas-sesiones_virtuales_por_profesional/{id_profesional}"
    response = client.get(url)

    print("🔍 Status code (no existe):", response.status_code)
    assert response.status_code == 500
    assert response.json()["detail"] == "Error interno del servidor."
