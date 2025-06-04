import os
import sys
import json
from fastapi.testclient import TestClient

# ✅ Asegura que el módulo app se pueda importar correctamente
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

def test_obtener_distritos_por_servicio():
    id_servicio = 2  # Reemplaza con un ID real de tu base de datos
    url = f"/api/services/usuario/servicio/{id_servicio}/distritos"

    response = client.get(url)

    print("🔍 Status code:", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2))

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert all("id_distrito" in d and "nombre" in d for d in data)
