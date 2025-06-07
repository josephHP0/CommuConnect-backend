import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Agrega la raíz del proyecto al path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

def test_es_plan_con_topes_visual():
    id_inscripcion = 10  # Cambia esto según la inscripción que quieras probar

    response = client.get(f"/api/billing/usuario/plan/{id_inscripcion}/es-con-topes")
    
    assert response.status_code == 200, f"Error HTTP: {response.text}"

    data = response.json()
    print(f"\n🧪 Respuesta para inscripción {id_inscripcion}:")
    print(json.dumps(data, indent=2))

    # Validación básica
    assert "esPlanConTopes" in data
    assert isinstance(data["esPlanConTopes"], bool)
