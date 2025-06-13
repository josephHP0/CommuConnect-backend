import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.modules.users.models import Usuario, Cliente
from app.modules.communities.models import Comunidad
from app.modules.services.models import Servicio, Local, ComunidadXServicio, Profesional
from app.modules.reservations.models import Sesion, SesionPresencial, Reserva, SesionVirtual
from utils.datetime_utils import convert_utc_to_local

def test_get_presencial_reservation_details(client: TestClient, session_test: Session, test_user_token: str):
    # 1. Setup: Create user and related data
    user = session_test.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).one()
    cliente = session_test.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).one()

    comunidad = Comunidad(nombre="Comunidad Detalle P", slogan="Test", creado_por="test")
    servicio = Servicio(nombre="Servicio Detalle P", descripcion="Test", creado_por="test", modalidad="Presencial", fecha_creacion=datetime.utcnow(), estado=1)
    local = Local(nombre="Local Detalle P", direccion_detallada="Av. Siempreviva 123", responsable="Juan Perez", id_departamento=14, id_distrito=1)
    
    session_test.add_all([comunidad, servicio, local])
    session_test.commit()
    session_test.refresh(comunidad)
    session_test.refresh(servicio)
    session_test.refresh(local)

    local.id_servicio = servicio.id_servicio # Link local to service
    comunidad_x_servicio = ComunidadXServicio(id_comunidad=comunidad.id_comunidad, id_servicio=servicio.id_servicio)
    session_test.add_all([local, comunidad_x_servicio])

    fecha_inicio = datetime.utcnow() + timedelta(days=2)
    sesion = Sesion(id_servicio=servicio.id_servicio, descripcion="Sesión presencial", inicio=fecha_inicio, fin=fecha_inicio + timedelta(hours=1), tipo="Presencial")
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)
    
    sesion_presencial = SesionPresencial(id_sesion=sesion.id_sesion, id_local=local.id_local, capacidad=10)
    reserva = Reserva(id_sesion=sesion.id_sesion, id_cliente=cliente.id_cliente, estado_reserva="confirmada")
    session_test.add_all([sesion_presencial, reserva])
    session_test.commit()
    session_test.refresh(reserva)

    # 2. Make the API call
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get(f"/api/reservations/{reserva.id_reserva}/details", headers=headers)

    # 3. Assertions
    assert response.status_code == 200, response.text
    data = response.json()
    
    local_inicio = convert_utc_to_local(fecha_inicio)
    
    assert data["nombre_servicio"] == servicio.nombre
    assert data["fecha"] == local_inicio.strftime("%d/%m/%Y")
    assert data["hora_inicio"] == local_inicio.strftime("%H:%M")
    assert data["tipo_sesion"] == "Presencial"
    assert data["responsable"] == local.responsable
    assert data["nombre_local"] == local.nombre
    assert data["direccion"] == local.direccion_detallada
    assert data["url_meeting"] is None
    assert data["nombre_profesional"] is None
    assert data["formulario_completado"] is False

def test_get_virtual_reservation_details(client: TestClient, session_test: Session, test_user_token: str):
    # 1. Setup
    user = session_test.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).one()
    cliente = session_test.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).one()

    comunidad = Comunidad(nombre="Comunidad Detalle V", slogan="Test", creado_por="test")
    servicio = Servicio(nombre="Servicio Detalle V", descripcion="Test", creado_por="test", modalidad="Virtual", fecha_creacion=datetime.utcnow(), estado=1)
    profesional = Profesional(nombre_completo="Ana Lopez", formulario="http://forms.example/ana")

    session_test.add_all([comunidad, servicio, profesional])
    session_test.commit()
    session_test.refresh(comunidad)
    session_test.refresh(servicio)
    session_test.refresh(profesional)

    profesional.id_servicio = servicio.id_servicio
    comunidad_x_servicio = ComunidadXServicio(id_comunidad=comunidad.id_comunidad, id_servicio=servicio.id_servicio)
    session_test.add_all([profesional, comunidad_x_servicio])

    fecha_inicio = datetime.utcnow() + timedelta(days=2)
    sesion = Sesion(id_servicio=servicio.id_servicio, descripcion="Sesión virtual", inicio=fecha_inicio, fin=fecha_inicio + timedelta(hours=1), tipo="Virtual")
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)
    
    sesion_virtual = SesionVirtual(id_sesion=sesion.id_sesion, id_profesional=profesional.id_profesional, url_meeting="http://zoom.example/meeting/123")
    reserva = Reserva(id_sesion=sesion.id_sesion, id_cliente=cliente.id_cliente, estado_reserva="confirmada", archivo=None)
    session_test.add_all([sesion_virtual, reserva])
    session_test.commit()
    session_test.refresh(reserva)

    # 2. Make the API call
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get(f"/api/reservations/{reserva.id_reserva}/details", headers=headers)

    # 3. Assertions
    assert response.status_code == 200, response.text
    data = response.json()
    
    local_inicio = convert_utc_to_local(fecha_inicio)
    
    assert data["nombre_servicio"] == servicio.nombre
    assert data["fecha"] == local_inicio.strftime("%d/%m/%Y")
    assert data["hora_inicio"] == local_inicio.strftime("%H:%M")
    assert data["tipo_sesion"] == "Virtual"
    assert data["responsable"] is None # Based on user's last change
    assert data["nombre_profesional"] == profesional.nombre_completo
    assert data["url_meeting"] == sesion_virtual.url_meeting
    assert data["nombre_local"] is None
    assert data["direccion"] is None
    assert data["formulario_completado"] is False

def test_get_virtual_reservation_details_form_completed(client: TestClient, session_test: Session, test_user_token: str):
    # 1. Setup
    user = session_test.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).one()
    cliente = session_test.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).one()

    comunidad = Comunidad(nombre="Comunidad Detalle VC", slogan="Test", creado_por="test")
    servicio = Servicio(nombre="Servicio Detalle VC", descripcion="Test", creado_por="test", modalidad="Virtual", fecha_creacion=datetime.utcnow(), estado=1)
    profesional = Profesional(nombre_completo="Carlos Diaz", formulario="http://forms.example/carlos")

    session_test.add_all([comunidad, servicio, profesional])
    session_test.commit()
    session_test.refresh(comunidad); session_test.refresh(servicio); session_test.refresh(profesional)

    profesional.id_servicio = servicio.id_servicio
    comunidad_x_servicio = ComunidadXServicio(id_comunidad=comunidad.id_comunidad, id_servicio=servicio.id_servicio)
    session_test.add_all([profesional, comunidad_x_servicio])

    fecha_inicio = datetime.utcnow() + timedelta(days=2)
    sesion = Sesion(id_servicio=servicio.id_servicio, descripcion="Sesión virtual completada", inicio=fecha_inicio, fin=fecha_inicio + timedelta(hours=1), tipo="Virtual")
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)
    
    # Create reservation WITH file
    sesion_virtual = SesionVirtual(id_sesion=sesion.id_sesion, id_profesional=profesional.id_profesional, url_meeting="http://zoom.example/meeting/456")
    reserva = Reserva(id_sesion=sesion.id_sesion, id_cliente=cliente.id_cliente, estado_reserva="confirmada", archivo=b"dummy file content")
    session_test.add_all([sesion_virtual, reserva])
    session_test.commit()
    session_test.refresh(reserva)

    # 2. Make the API call
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get(f"/api/reservations/{reserva.id_reserva}/details", headers=headers)

    # 3. Assertions
    assert response.status_code == 200, response.text
    data = response.json()
    local_inicio = convert_utc_to_local(fecha_inicio)
    assert data["fecha"] == local_inicio.strftime("%d/%m/%Y")
    assert data["formulario_completado"] is True

def test_get_reservation_details_not_found(client: TestClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get("/api/reservations/99999/details", headers=headers)
    assert response.status_code == 404
    assert "Reserva no encontrada" in response.json()["detail"] 