import os
import sys
import json
from fastapi.testclient import TestClient

#Asegura que el módulo app se pueda importar correctamente
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

def test_obtener_locales_por_servicio_y_distrito():
    id_servicio = 2     #Asegúrate de que exista en tu base
    id_distrito = 20    #Asegúrate de que exista y tenga locales activos

    url = f"/api/services/servicio/{id_servicio}/distrito/{id_distrito}/locales"


    response = client.get(url)

    print("🔍 Status code:", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if data:
        for local in data:
            assert "id_local" in local
            assert "nombre" in local
            assert "direccion_detallada" in local
            assert "responsable" in local
            assert "link" in local
