# tests/integration/test_form_endpoints.py

import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, delete
from app.modules.reservations.models import Reserva, Sesion, SesionVirtual
from app.modules.services.models import Profesional
from app.modules.users.models import Cliente, Usuario
from app.core.db import get_session, engine
from app.main import app
from datetime import datetime, timedelta, timezone
import shutil
from app.core.security import hash_password
from app.core.enums import TipoUsuario, TipoDocumento
import random

# Configura entorno
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

client = TestClient(app)

LOGIN_DATA = {"email": "testcliente@example.com", "password": "password"}

@pytest.fixture(scope="module", autouse=True)
def setup_teardown_module():
    # Define variables to hold the created objects
    profesional = None
    cliente_user = None
    cliente = None
    sesion = None
    sesion_virtual = None
    reserva = None
    rand_id = random.randint(0, 99999)

    # Use a single session for setup and yield
    with Session(engine) as session:
        # Create Profesional
        profesional = Profesional(
            nombre_completo="Test Profesional",
            email=f"testprofesional{rand_id}@example.com",
            id_servicio=6
        )
        session.add(profesional)
        session.commit()
        session.refresh(profesional)

        # Create Cliente User
        cliente_user = Usuario(
            nombre="Test",
            apellido="Cliente",
            email=f"testcliente{rand_id}@example.com",
            password=hash_password(LOGIN_DATA["password"]),
            tipo=TipoUsuario.Cliente
        )
        session.add(cliente_user)
        session.commit()
        session.refresh(cliente_user)
        
        cliente = Cliente(
            id_usuario=cliente_user.id_usuario, 
            id_distrito=1, 
            id_departamento=1,
            tipo_documento=TipoDocumento.DNI,
            num_doc=f"12345{rand_id}",
            numero_telefono="987654321",
            talla=170,
            peso=70
        )
        session.add(cliente)
        session.commit()
        session.refresh(cliente)

        # Create Virtual Session
        now = datetime.now(timezone.utc)
        sesion = Sesion(
            inicio=now + timedelta(days=2),
            fin=now + timedelta(days=2, hours=1),
            tipo="Virtual",
            id_servicio=6,
            descripcion="Test session for form"
        )
        session.add(sesion)
        session.commit()
        session.refresh(sesion)

        sesion_virtual = SesionVirtual(
            id_sesion=sesion.id_sesion,
            id_profesional=profesional.id_profesional,
            url_archivo="http://example.com/form-link"
        )
        session.add(sesion_virtual)
        session.commit()
        session.refresh(sesion_virtual)

        # Create Reservation
        reserva = Reserva(
            id_cliente=cliente.id_cliente,
            id_sesion=sesion.id_sesion,
            id_comunidad=1,
            estado="Confirmada"
        )
        session.add(reserva)
        session.commit()
        session.refresh(reserva)
        
        yield {
            "profesional_id": profesional.id_profesional,
            "cliente_id": cliente.id_cliente,
            "sesion_id": sesion.id_sesion,
            "reserva_id": reserva.id_reserva,
            "login_email": cliente_user.email
        }

        # Teardown: clean up test data within the same session
        if reserva:
            session.exec(delete(Reserva).where(Reserva.id_reserva == reserva.id_reserva))
        if sesion_virtual:
            session.exec(delete(SesionVirtual).where(SesionVirtual.id_sesion_virtual == sesion_virtual.id_sesion_virtual))
        if sesion:
            session.exec(delete(Sesion).where(Sesion.id_sesion == sesion.id_sesion))
        if profesional:
            session.exec(delete(Profesional).where(Profesional.id_profesional == profesional.id_profesional))
        if cliente:
            session.exec(delete(Cliente).where(Cliente.id_cliente == cliente.id_cliente))
        if cliente_user:
            session.exec(delete(Usuario).where(Usuario.id_usuario == cliente_user.id_usuario))
        
        session.commit()


def get_auth_headers(client, email):
    login_data = {"email": email, "password": LOGIN_DATA["password"]}
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_form_info(setup_teardown_module):
    sesion_id = setup_teardown_module["sesion_id"]
    headers = get_auth_headers(client, setup_teardown_module["login_email"])
    
    response = client.get(f"/api/reservations/formulario/{sesion_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["profesional_nombre"] == "Test Profesional"
    assert "fecha_sesion" in data
    assert "hora_inicio" in data
    assert data["url_formulario"] == "http://example.com/form-link"
    assert data["formulario_completado"] is False

def test_submit_form(setup_teardown_module):
    sesion_id = setup_teardown_module["sesion_id"]
    headers = get_auth_headers(client, setup_teardown_module["login_email"])

    # Create a dummy file to upload
    file_path = "test_form.txt"
    with open(file_path, "w") as f:
        f.write("This is the content of the form.")

    with open(file_path, "rb") as f:
        files = {"file": ("test_form.txt", f, "text/plain")}
        response = client.post(
            f"/api/reservations/formulario/{sesion_id}/enviar",
            files=files,
            headers=headers,
        )

    os.remove(file_path) # Clean up the dummy file

    assert response.status_code == 200
    assert response.json()["mensaje"] == "Archivo enviado al profesional correspondiente."

    # Verify the form is marked as completed
    response_check = client.get(f"/api/reservations/formulario/{sesion_id}", headers=headers)
    assert response_check.status_code == 200
    assert response_check.json()["formulario_completado"] is True

def test_submit_form_for_non_existent_session(setup_teardown_module):
    headers = get_auth_headers(client, setup_teardown_module["login_email"])
    non_existent_sesion_id = 99999

    file_path = "test_form_not_exists.txt"
    with open(file_path, "w") as f:
        f.write("content")
    
    with open(file_path, "rb") as f:
        files = {"file": ("test_form_not_exists.txt", f, "text/plain")}
        response = client.post(
            f"/api/reservations/formulario/{non_existent_sesion_id}/enviar",
            files=files,
            headers=headers,
        )

    os.remove(file_path)

    assert response.status_code == 404
    assert "Sesión virtual no encontrada" in response.json()["detail"] 