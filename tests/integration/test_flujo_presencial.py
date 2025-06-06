# tests/test_endpoints.py
from fastapi.testclient import TestClient
from sqlmodel import Session
from datetime import datetime, date

def test_obtener_distritos_por_servicio(client: TestClient, session_test: Session):
    # 3) Llamar al endpoint
    response = client.get("/api/services/usuario/servicio/10/distritos")
    assert response.status_code == 200

    data = response.json()
    # Se espera una lista con 1 elemento
    assert isinstance(data, list)
    assert len(data) == 1

    # Verificamos que los IDs coincidan
    ids_obtenidos = {item["id_distrito"] for item in data}
    assert ids_obtenidos == {39}


def test_obtener_locales_por_servicio_y_distrito(client: TestClient, session_test: Session):

    # 4) Prueba “feliz”: debe devolver el local
    url = "/api/services/servicio/10/distrito/39/locales"
    response = client.get(url)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id_local"] == 5

    # 5) Prueba “no hay locales activos”: usar un distrito inexistente o sin locales
    url_no = "/api/services/servicio/2/distrito/999/locales"
    response_no = client.get(url_no)
    assert response_no.status_code == 404
    assert response_no.json()["detail"] == "No se encontraron locales activos para ese servicio y distrito."


def test_listar_fechas_presenciales(client: TestClient, session_test: Session):

    # 5) Llamar endpoint con parámetros correctos
    url = "/api/reservations/fechas-presenciales?id_servicio=10&id_distrito=39&id_local=5"
    response = client.get(url)
    assert response.status_code == 200

    data = response.json()
    # Debe tener el campo “fechas” con una lista ordenada de strings “YYYY-MM-DD”
    assert "fechas" in data
    fechas = data["fechas"]
    assert isinstance(fechas, list)
    assert fechas == ["10/06/2025", "12/06/2025"]

    # 6) Parámetros incorrectos (distrito equivocado) → 404
    url_err = "/api/reservations/fechas-presenciales?id_servicio=10&id_distrito=39&id_local=100"
    response_err = client.get(url_err)
    assert response_err.status_code == 404
    assert response_err.json()["detail"] == "El local no existe o no pertenece al distrito indicado"


def test_listar_horas_presenciales(client: TestClient, session_test: Session):

    # 3) Llamar correctamente con fecha 
    url = "/api/reservations/horas-presenciales?id_servicio=10&id_distrito=39&id_local=5&fecha=10/06/2025"
    response = client.get(url)
    assert response.status_code == 200

    data = response.json()
    assert "horas" in data
    horas = data["horas"]
    assert isinstance(horas, list)
    assert horas == ["09:00"]

    # 4) Fecha en formato inválido (“YYYY-MM-DD” en vez de “DD/MM/YYYY”)
    url_bad = "/api/reservations/horas-presenciales?id_servicio=6&id_distrito=60&id_local=600&fecha=2025-06-12"
    response_bad = client.get(url_bad)
    assert response_bad.status_code == 400
    assert "Formato inválido para 'fecha'" in response_bad.json()["detail"]

    # 5) Local no existe en ese distrito → 404
    url_nf = "/api/reservations/horas-presenciales?id_servicio=10&id_distrito=39&id_local=600&fecha=12/06/2025"
    response_nf = client.get(url_nf)
    assert response_nf.status_code == 404


def test_sesiones_presenciales_detalladas(client: TestClient, session_test: Session):

    # 3) Llamada correcta con fecha “2025-06-18” y hora “08:00”
    url = "/api/reservations/sesiones-presenciales?id_servicio=10&id_distrito=39&id_local=5&fecha=10/06/2025&hora=09:00"
    response = client.get(url)
    assert response.status_code == 200

    data = response.json()
    assert "sesiones" in data
    sesiones = data["sesiones"]
    assert isinstance(sesiones, list)
    # Debe devolver exactamente 1 sesion
    assert len(sesiones) == 1

    print(sesiones[0])

    # 4) Mismo local pero hora distinta = []
    url= "/api/reservations/sesiones-presenciales?id_servicio=10&id_distrito=39&id_local=5&fecha=12/06/2025&hora=17:00"
    response = client.get(url)
    assert response.status_code == 200

    data = response.json()
    assert "sesiones" in data
    sesiones = data["sesiones"]
    assert isinstance(sesiones, list)
    # Debe devolver exactamente 1 sesion
    assert len(sesiones) == 1

    print(sesiones[0])

    # 5) Local no existe o no pertenece = 404
    url_nf = "/api/reservations/sesiones-presenciales?id_servicio=10&id_distrito=39&id_local=700&fecha=18/06/2025&hora=08:00"
    response_nf = client.get(url_nf)
    assert response_nf.status_code == 404
    assert response_nf.json()["detail"] == "El local no existe o no pertenece al distrito indicado"
