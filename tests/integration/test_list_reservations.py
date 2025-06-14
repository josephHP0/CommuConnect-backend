import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta
from utils.datetime_utils import convert_utc_to_local

# Re-using test data and user creation logic can be done by importing from conftest or another shared module
# For simplicity here, we define what's needed.

def test_list_reservations_by_user_community(client: TestClient, session_test: Session, test_user_token: str):
    # This test depends on the `test_user_token` fixture which should handle user creation and token generation.
    # We need to get the created user and client from the database.
    from app.modules.users.models import Usuario, Cliente
    user = session_test.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).one()
    cliente = session_test.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).one()

    # 1. Setup: Create necessary entities
    from app.modules.communities.models import Comunidad
    from app.modules.services.models import Servicio, ComunidadXServicio
    from app.modules.reservations.models import Sesion, Reserva

    # Create a community
    comunidad = Comunidad(nombre="Comunidad de Prueba Listar", slogan="Test", creado_por="test")
    session_test.add(comunidad)
    session_test.commit()
    session_test.refresh(comunidad)

    # Create a service
    servicio = Servicio(nombre="Servicio de Prueba Listar", descripcion="Test", creado_por="test", modalidad="Virtual")
    session_test.add(servicio)
    session_test.commit()
    session_test.refresh(servicio)

    # Link service to community
    comunidad_x_servicio = ComunidadXServicio(id_comunidad=comunidad.id_comunidad, id_servicio=servicio.id_servicio)
    session_test.add(comunidad_x_servicio)
    session_test.commit()

    # Create a session for that service
    fecha_inicio = datetime.utcnow() + timedelta(days=3)
    sesion = Sesion(
        id_servicio=servicio.id_servicio,
        descripcion="Sesión para listar",
        inicio=fecha_inicio,
        fin=fecha_inicio + timedelta(hours=1),
        tipo="Virtual",
        creado_por="test"
    )
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)

    # Create a reservation for the user in that session
    reserva = Reserva(
        id_sesion=sesion.id_sesion,
        id_cliente=cliente.id_cliente,
        estado_reserva="confirmada"
    )
    session_test.add(reserva)
    session_test.commit()
    session_test.refresh(reserva)

    # 2. Make the API call
    headers = {"Authorization": f"Bearer {test_user_token}"}
    start_date_str = (datetime.utcnow() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    response = client.get(
        f"/api/reservations/by-user-community?id_comunidad={comunidad.id_comunidad}&fecha={start_date_str}",
        headers=headers
    )

    # 3. Assertions
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    
    assert "reservas" in data
    assert len(data["reservas"]) == 1
    
    reserva_resp = data["reservas"][0]
    assert reserva_resp["id_reserva"] == reserva.id_reserva
    assert reserva_resp["nombre_servicio"] == servicio.nombre
    
    # Convertir la fecha original a la zona horaria local para la comparación
    local_fecha_inicio = convert_utc_to_local(fecha_inicio)
    expected_fecha = local_fecha_inicio.strftime("%d/%m/%Y")
    expected_hora_inicio = local_fecha_inicio.strftime("%H:%M")
    
    assert reserva_resp["fecha"] == expected_fecha
    assert reserva_resp["hora_inicio"] == expected_hora_inicio

def test_list_reservations_empty_for_no_reservations(client: TestClient, session_test: Session, test_user_token: str):
    from app.modules.communities.models import Comunidad
    
    comunidad = Comunidad(nombre="Comunidad Vacía", slogan="Test", creado_por="test")
    session_test.add(comunidad)
    session_test.commit()
    session_test.refresh(comunidad)

    headers = {"Authorization": f"Bearer {test_user_token}"}
    start_date_str = datetime.utcnow().strftime("%d/%m/%Y")
    
    response = client.get(
        f"/api/reservations/by-user-community?id_comunidad={comunidad.id_comunidad}&fecha={start_date_str}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reservas"] == []

def test_list_reservations_invalid_date_format(client: TestClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get(
        "/api/reservations/by-user-community?id_comunidad=1&fecha=2024-01-01",
        headers=headers
    )
    assert response.status_code == 400
    assert "Formato inválido" in response.json()["detail"]

def test_list_reservations_outside_date_range(client: TestClient, session_test: Session, test_user_token: str):
    from app.modules.users.models import Usuario, Cliente
    from app.modules.communities.models import Comunidad
    from app.modules.services.models import Servicio, ComunidadXServicio
    from app.modules.reservations.models import Sesion, Reserva

    user = session_test.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).one()
    cliente = session_test.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).one()
    comunidad = Comunidad(nombre="Comunidad Fuera de Rango", slogan="Test", creado_por="test")
    session_test.add(comunidad)
    session_test.commit()
    session_test.refresh(comunidad)

    servicio = Servicio(nombre="Servicio Fuera de Rango", descripcion="Test", creado_por="test", modalidad="Virtual")
    session_test.add(servicio)
    session_test.commit()
    session_test.refresh(servicio)

    comunidad_x_servicio = ComunidadXServicio(id_comunidad=comunidad.id_comunidad, id_servicio=servicio.id_servicio)
    session_test.add(comunidad_x_servicio)
    session_test.commit()

    # Create a session 8 days from now
    fecha_inicio = datetime.utcnow() + timedelta(days=8)
    sesion = Sesion(id_servicio=servicio.id_servicio, descripcion="Sesión Lejana", inicio=fecha_inicio, fin=fecha_inicio + timedelta(hours=1))
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)

    reserva = Reserva(id_sesion=sesion.id_sesion, id_cliente=cliente.id_cliente, estado_reserva="confirmada")
    session_test.add(reserva)
    session_test.commit()

    headers = {"Authorization": f"Bearer {test_user_token}"}
    start_date_str = datetime.utcnow().strftime("%d/%m/%Y")
    
    response = client.get(
        f"/api/reservations/by-user-community?id_comunidad={comunidad.id_comunidad}&fecha={start_date_str}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reservas"] == [] 