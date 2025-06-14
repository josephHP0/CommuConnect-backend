import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlmodel import Session, select, delete
from app.modules.reservations.models import Reserva, Sesion, SesionVirtual, SesionPresencial
from app.modules.services.models import Servicio, ComunidadXServicio
from app.modules.communities.models import Comunidad
from app.modules.users.models import Cliente, Usuario
from app.modules.reservations.services import crear_sesion_con_tipo
from sqlalchemy import delete
from datetime import datetime, timedelta, timezone

def _create_base_scenario(session: Session):
    """Creates two communities and two services, linking one service to each."""
    comunidad_a = Comunidad(nombre="Comunidad A")
    comunidad_b = Comunidad(nombre="Comunidad B")
    
    servicio_yoga = Servicio(nombre="Servicio Yoga")
    servicio_meditacion = Servicio(nombre="Servicio Meditación")
    
    session.add(comunidad_a)
    session.add(comunidad_b)
    session.add(servicio_yoga)
    session.add(servicio_meditacion)
    session.commit()

    # Associate services with communities
    session.add(ComunidadXServicio(id_comunidad=comunidad_a.id_comunidad, id_servicio=servicio_yoga.id_servicio))
    session.add(ComunidadXServicio(id_comunidad=comunidad_b.id_comunidad, id_servicio=servicio_meditacion.id_servicio))
    session.commit()

    return {
        "comunidad1_id": comunidad_a.id_comunidad,
        "comunidad2_id": comunidad_b.id_comunidad,
        "servicio1_id": servicio_yoga.id_servicio,
        "servicio2_id": servicio_meditacion.id_servicio,
    }

def _create_reservation_for_test(session: Session, cliente_id: int, sesion_id: int, id_comunidad: int) -> Reserva:
    """Helper to create a reservation for an existing session."""

    reserva = Reserva(
        id_sesion=sesion_id,
        id_cliente=cliente_id,
        id_comunidad=id_comunidad,
        estado_reserva="confirmada",
        fecha_reservada=datetime.now(timezone.utc), # This date will be overridden by the actual session start time if the API does its job
        creado_por=1 # Assuming a default user for test data creation
    )
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    return reserva

def cleanup_test_data(session: Session, 
                        reservation_ids: list = None, 
                        session_ids: list = None, 
                        community_ids: list = None, 
                        service_ids: list = None):
    """Cleans up all data created for a test."""
    
    # Fetch objects by ID to ensure they are "fresh" in the session before deletion
    reservations_to_delete = session.exec(select(Reserva).where(Reserva.id_reserva.in_(reservation_ids))).all() if reservation_ids else []
    sessions_to_delete = session.exec(select(Sesion).where(Sesion.id_sesion.in_(session_ids))).all() if session_ids else []
    communities_to_delete = session.exec(select(Comunidad).where(Comunidad.id_comunidad.in_(community_ids))).all() if community_ids else []
    services_to_delete = session.exec(select(Servicio).where(Servicio.id_servicio.in_(service_ids))).all() if service_ids else []

    # 1. Delete Reservations (children of Session, Cliente, Comunidad)
    for res in reservations_to_delete:
        session.delete(res)

    # 2. Delete SesionVirtual objects (children of Sesion)
    # Need to explicitly delete SesionVirtual as no cascade is defined from Sesion
    for ses in sessions_to_delete:
        virtual_session = session.exec(select(SesionVirtual).where(SesionVirtual.id_sesion == ses.id_sesion)).first()
        if virtual_session:
            session.delete(virtual_session)

    # 3. Delete SesionPresencial objects (children of Sesion)
    # Need to explicitly delete SesionPresencial as no cascade is defined from Sesion
    for ses in sessions_to_delete:
        presencial_session = session.exec(select(SesionPresencial).where(SesionPresencial.id_sesion == ses.id_sesion)).first()
        if presencial_session:
            session.delete(presencial_session)
    
    # 4. Delete Sesion objects (parent of Reserva, SesionVirtual, SesionPresencial)
    for ses in sessions_to_delete:
        session.delete(ses)

    # 5. Delete ComunidadXServicio associations (children of Comunidad, Servicio)
    if community_ids and service_ids:
        session.exec(delete(ComunidadXServicio).where(
            ComunidadXServicio.id_comunidad.in_(community_ids),
            ComunidadXServicio.id_servicio.in_(service_ids)
        ))
    elif community_ids:
         session.exec(delete(ComunidadXServicio).where(
            ComunidadXServicio.id_comunidad.in_(community_ids)
        ))
    elif service_ids:
        session.exec(delete(ComunidadXServicio).where(
            ComunidadXServicio.id_servicio.in_(service_ids)
        ))

    # 6. Delete Communities (parent of ComunidadXServicio)
    for comm in communities_to_delete:
        session.delete(comm)

    # 7. Delete Services (parent of ComunidadXServicio, Sesion)
    for serv in services_to_delete:
        session.delete(serv)

def test_reservation_conflict_in_same_community(client: TestClient, session_test: Session, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    cliente = session_test.exec(select(Cliente).where(Cliente.num_doc == "12345678")).first()
    assert cliente, "Test client not found."

    scenario = _create_base_scenario(session_test)
    
    # 1. Create an initial reservation for tomorrow at 10 AM in Comunidad A
    start_time_reserva1 = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    sesion1 = crear_sesion_con_tipo(
        session=session_test,
        id_servicio=scenario["servicio1_id"],
        tipo="Virtual",
        descripcion="Test Session",
        inicio=start_time_reserva1,
        fin=start_time_reserva1 + timedelta(hours=1),
        url_archivo="https://test.com/virtual_session_1.pdf"
    )

    # Create the reservation directly
    reserva1 = Reserva(
        id_sesion=sesion1.id_sesion,
        id_cliente=cliente.id_cliente,
        id_comunidad=scenario["comunidad1_id"],
        estado_reserva="confirmada",
        fecha_reservada=sesion1.inicio,
        creado_por=1
    )
    session_test.add(reserva1)
    session_test.commit()
    session_test.refresh(reserva1)

    # 2. Attempt to create an overlapping reservation (tomorrow at 10:30 AM) in the SAME community
    start_time_reserva_conflict = start_time_reserva1 + timedelta(minutes=30)
    sesion_conflictiva = crear_sesion_con_tipo(
        session=session_test,
        id_servicio=scenario["servicio1_id"],
        tipo="Virtual",
        descripcion="Sesión conflictiva",
        inicio=start_time_reserva_conflict,
        fin=start_time_reserva_conflict + timedelta(hours=1),
        url_archivo="https://test.com/virtual_session_conflict.pdf"
    )

    response = client.post("/api/reservations/virtual", headers=headers, json={"id_sesion": sesion_conflictiva.id_sesion, "id_comunidad": scenario["comunidad1_id"]})

    assert response.status_code == 409
    assert "Ya tienes otra sesión activa que se cruza con ese horario en esta comunidad." in response.json()["detail"]

    # Cleanup
    cleanup_test_data(session_test, 
        reservation_ids=[reserva1.id_reserva], 
        session_ids=[sesion1.id_sesion, sesion_conflictiva.id_sesion], 
        community_ids=[scenario["comunidad1_id"]], 
        service_ids=[scenario["servicio1_id"]])

def test_no_reservation_conflict_in_different_communities(client: TestClient, session_test: Session, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    cliente = session_test.exec(select(Cliente).where(Cliente.num_doc == "12345678")).first()

    assert cliente, "Test client not found."

    scenario = _create_base_scenario(session_test)

    # 1. Create an initial reservation in Comunidad A
    start_time_reserva1 = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    sesion1_comm_a = crear_sesion_con_tipo(
        session=session_test,
        id_servicio=scenario["servicio1_id"],
        tipo="Virtual",
        descripcion="Test Session Comunidad A",
        inicio=start_time_reserva1,
        fin=start_time_reserva1 + timedelta(hours=1),
        url_archivo="https://test.com/virtual_session_1_commA.pdf"
    )

    # Create the first reservation directly
    reserva1_comm_a = Reserva(
        id_sesion=sesion1_comm_a.id_sesion,
        id_cliente=cliente.id_cliente,
        id_comunidad=scenario["comunidad1_id"],
        estado_reserva="confirmada",
        fecha_reservada=sesion1_comm_a.inicio,
        creado_por=1
    )
    session_test.add(reserva1_comm_a)
    session_test.commit()
    session_test.refresh(reserva1_comm_a)

    # 2. Attempt to create an overlapping reservation in a DIFFERENT community (Comunidad B)
    start_time_reserva2 = start_time_reserva1 + timedelta(minutes=30)
    
    # Use the new service function to create the session and its virtual counterpart
    sesion_sin_conflicto_comm_b = crear_sesion_con_tipo(
        session=session_test,
        id_servicio=scenario["servicio2_id"],
        tipo="Virtual",
        descripcion="Sesión sin conflicto Comunidad B",
        inicio=start_time_reserva2,
        fin=start_time_reserva2 + timedelta(hours=1),
        url_archivo="https://test.com/virtual_session_2.pdf"
    )

    response = client.post("/api/reservations/virtual", headers=headers, json={"id_sesion": sesion_sin_conflicto_comm_b.id_sesion, "id_comunidad": scenario["comunidad2_id"]})
    
    # Assert that the reservation is created successfully
    assert response.status_code == 201
    reserva2_comm_b_id = response.json()["id_reserva"]
    
    # Cleanup
    cleanup_test_data(session_test, 
        reservation_ids=[reserva1_comm_a.id_reserva, reserva2_comm_b_id], 
        session_ids=[sesion1_comm_a.id_sesion, sesion_sin_conflicto_comm_b.id_sesion], 
        community_ids=[scenario["comunidad1_id"], scenario["comunidad2_id"]], 
        service_ids=[scenario["servicio1_id"], scenario["servicio2_id"]]) 