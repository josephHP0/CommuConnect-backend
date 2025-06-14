import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.modules.reservations.models import Reserva, Sesion
from app.modules.services.models import Servicio, ComunidadXServicio
from app.modules.communities.models import Comunidad
from app.modules.users.models import Cliente
from datetime import datetime, timedelta

def _create_base_scenario(session: Session):
    """Creates two communities and two services, linking one service to each."""
    comunidad1 = Comunidad(nombre="Comunidad A")
    comunidad2 = Comunidad(nombre="Comunidad B")
    
    servicio1 = Servicio(nombre="Servicio Yoga")
    servicio2 = Servicio(nombre="Servicio Meditación")
    
    session.add_all([comunidad1, comunidad2, servicio1, servicio2])
    session.commit()
    
    session.add(ComunidadXServicio(id_comunidad=comunidad1.id_comunidad, id_servicio=servicio1.id_servicio))
    session.add(ComunidadXServicio(id_comunidad=comunidad2.id_comunidad, id_servicio=servicio2.id_servicio))
    session.commit()

    # Assertions to ensure data integrity
    assert comunidad1.id_comunidad != comunidad2.id_comunidad
    assert servicio1.id_servicio != servicio2.id_servicio
    
    link1 = session.exec(select(ComunidadXServicio).where(ComunidadXServicio.id_servicio == servicio1.id_servicio)).all()
    assert len(link1) == 1
    assert link1[0].id_comunidad == comunidad1.id_comunidad

    link2 = session.exec(select(ComunidadXServicio).where(ComunidadXServicio.id_servicio == servicio2.id_servicio)).all()
    assert len(link2) == 1
    assert link2[0].id_comunidad == comunidad2.id_comunidad
    
    return {
        "comunidad1_id": comunidad1.id_comunidad, "servicio1_id": servicio1.id_servicio,
        "comunidad2_id": comunidad2.id_comunidad, "servicio2_id": servicio2.id_servicio
    }

def _create_reservation_for_test(session: Session, client_id: int, service_id: int, start_time: datetime):
    """Helper to create a session and a reservation."""
    sesion = Sesion(
        id_servicio=service_id,
        tipo="Presencial",
        descripcion="Test Session",
        inicio=start_time,
        fin=start_time + timedelta(hours=1),
    )
    session.add(sesion)
    session.commit()
    
    reserva = Reserva(
        id_sesion=sesion.id_sesion,
        id_cliente=client_id,
        estado_reserva="confirmada",
    )
    session.add(reserva)
    session.commit()
    
    return sesion

def test_reservation_conflict_in_same_community(client: TestClient, session_test: Session, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    cliente = session_test.exec(select(Cliente).where(Cliente.num_doc == "12345678")).first()
    assert cliente, "Test client not found."

    scenario = _create_base_scenario(session_test)
    
    # 1. Create an initial reservation for tomorrow at 10 AM in Comunidad A
    start_time_reserva1 = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    _create_reservation_for_test(session_test, cliente.id_cliente, scenario["servicio1_id"], start_time_reserva1)

    # 2. Attempt to create an overlapping reservation (tomorrow at 10:30 AM) in the SAME community
    start_time_reserva2 = start_time_reserva1 + timedelta(minutes=30)
    sesion_conflictiva = Sesion(
        id_servicio=scenario["servicio1_id"], 
        descripcion="Sesión conflictiva",
        inicio=start_time_reserva2, 
        fin=start_time_reserva2 + timedelta(hours=1)
    )
    session_test.add(sesion_conflictiva)
    session_test.commit()

    response = client.post("/api/reservations/", headers=headers, json={"id_sesion": sesion_conflictiva.id_sesion})
    
    # Assert that the API correctly identifies the conflict
    assert response.status_code == 400
    assert "Tienes otra reserva que se cruza con este horario" in response.json()["detail"]

def test_no_reservation_conflict_in_different_communities(client: TestClient, session_test: Session, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    cliente = session_test.exec(select(Cliente).where(Cliente.num_doc == "12345678")).first()
    assert cliente, "Test client not found."

    scenario = _create_base_scenario(session_test)
    
    # 1. Create an initial reservation for tomorrow at 10 AM in Comunidad A
    start_time_reserva1 = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    _create_reservation_for_test(session_test, cliente.id_cliente, scenario["servicio1_id"], start_time_reserva1)

    # 2. Attempt to create an overlapping reservation (10:30 AM) in a DIFFERENT community (Comunidad B)
    start_time_reserva2 = start_time_reserva1 + timedelta(minutes=30)
    sesion_sin_conflicto = Sesion(
        id_servicio=scenario["servicio2_id"], # Using servicio2 from comunidad2
        descripcion="Sesión sin conflicto",
        inicio=start_time_reserva2, 
        fin=start_time_reserva2 + timedelta(hours=1)
    )
    session_test.add(sesion_sin_conflicto)
    session_test.commit()

    response = client.post("/api/reservations/", headers=headers, json={"id_sesion": sesion_sin_conflicto.id_sesion})
    
    # Assert that the reservation is created successfully
    assert response.status_code == 201
    assert response.json()["id_reserva"] is not None 