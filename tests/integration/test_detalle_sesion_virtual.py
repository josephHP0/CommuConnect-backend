import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate que este es el entrypoint correcto

client = TestClient(app)

@pytest.mark.parametrize("id_sesion_virtual", [3])  # Puedes agregar más IDs si gustas
def test_detalle_sesion_virtual(id_sesion_virtual):
    response = client.get(f"/api/services/sesiones-virtuales/{id_sesion_virtual}/detalle")
    print("\nJSON de respuesta:")
    print(response.json())
    assert response.status_code == 200, f"Error: {response.json()}"

    data = response.json()

    # Verifica que las claves importantes estén en la respuesta
    assert "id_sesion_virtual" in data
    assert "descripcion" in data
    assert "fecha" in data
    assert "hora_inicio" in data
    assert "hora_fin" in data
    assert "profesional" in data
    assert "inscritos" in data

    # Validación del profesional
    profesional = data["profesional"]
    assert "nombre" in profesional
    assert "apellido" in profesional
    assert "email" in profesional

    # Validación de al menos un inscrito si existe
    if data["inscritos"]:
        inscrito = data["inscritos"][0]
        assert "nombre" in inscrito
        assert "apellido" in inscrito
        assert "comunidad" in inscrito
        assert "entrego_archivo" in inscrito
