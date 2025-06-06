import os
import sys
import json
from fastapi.testclient import TestClient

# Asegura que el módulo app se pueda importar correctamente
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

def test_listar_profesionales_por_servicio():
    id_servicio = 1  # Asegúrate que exista y tenga profesionales en tu base de datos

    url = f"/api/services/profesionales/{id_servicio}"
    response = client.get(url)

    print("🔍 Status code:", response.status_code)
    print("🧾 Respuesta JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if data:
        for profesional in data:
            assert "id_profesional" in profesional
            assert "nombre_completo" in profesional
            assert "id_servicio" in profesional
            assert "formulario" in profesional
            assert "fecha_creacion" in profesional
            assert "creado_por" in profesional
            assert "fecha_modificacion" in profesional
            assert "modificado_por" in profesional
            assert "estado" in profesional


def test_listar_profesionales_por_servicio_no_existente():
    id_servicio = 9999  # Suponiendo que no existe
    url = f"/api/services/profesionales/{id_servicio}"
    response = client.get(url)

    assert response.status_code == 200  # o 404 si lo manejas así
    assert response.json() == []
