import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.modules.reservations.models import Reserva, Sesion
from app.modules.services.models import Servicio
from app.modules.communities.models import Comunidad
from app.modules.users.models import Cliente
from datetime import datetime, timedelta

# Note: Fixtures like `async_client`, `admin_token`, `client`, `session_test`, 
# and `test_user_token` are provided by `tests/conftest.py`

def _create_test_reservation(session: Session, client_id: int):
    """Helper to create a session and a reservation for it."""
    # Find a service and community to use
    servicio = session.exec(select(Servicio)).first()
    if not servicio:
        pytest.fail("No services found in DB. Cannot create reservation for test.")
    
    comunidad = session.exec(select(Comunidad)).first()
    if not comunidad:
        pytest.fail("No communities found in DB. Cannot create reservation for test.")

    # Create a session for tomorrow
    sesion = Sesion(
        id_servicio=servicio.id_servicio,
        tipo="Presencial",
        descripcion="Test Session for Cancellation Flow",
        inicio=datetime.utcnow() + timedelta(days=1),
        fin=datetime.utcnow() + timedelta(days=1, hours=1),
    )
    session.add(sesion)
    session.commit()
    session.refresh(sesion)

    # Create a confirmed reservation for that session
    reserva = Reserva(
        id_sesion=sesion.id_sesion,
        id_cliente=client_id,
        estado_reserva="confirmada",
    )
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    
    return reserva, comunidad.id_comunidad

def test_reservation_cancellation_flow(client: TestClient, session_test: Session, test_user_token: str):
    """
    Simulates the full user flow:
    1. A client user is created and logged in via fixtures.
    2. A reservation is created for this user.
    3. Verify the reservation is visible.
    4. Cancel the reservation.
    5. Verify the reservation is no longer visible.
    """
    # Step 1: User is already created and logged in by test_user_token
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Find the Cliente record for the user created by the fixture
    cliente = session_test.exec(
        select(Cliente).where(Cliente.num_doc == "12345678")
    ).first()
    assert cliente, "Test client could not be found in the database."

    reserva, id_comunidad = _create_test_reservation(session_test, cliente.id_cliente)
    
    # Step 2: Verify reservation is visible on the calendar
    tomorrow_date = (datetime.utcnow() + timedelta(days=1)).date()
    tomorrow_str = tomorrow_date.strftime("%d/%m/%Y")
    response = client.get(f"/api/reservations/by-user-community?id_comunidad={id_comunidad}&fecha={tomorrow_str}", headers=headers)
    assert response.status_code == 200
    
    reservas_visibles = response.json().get("reservas", [])
    assert any(r['id_reserva'] == reserva.id_reserva for r in reservas_visibles)

    # Step 3: Cancel the reservation
    cancel_response = client.patch(f"/api/reservations/{reserva.id_reserva}/cancel", headers=headers)
    assert cancel_response.status_code == 200
    assert cancel_response.json()["message"] == "Reserva cancelada exitosamente."

    # Step 4: Verify reservation is no longer visible on the calendar
    response_after_cancel = client.get(f"/api/reservations/by-user-community?id_comunidad={id_comunidad}&fecha={tomorrow_str}", headers=headers)
    assert response_after_cancel.status_code == 200
    
    reservas_despues_de_cancelar = response_after_cancel.json().get("reservas", [])
    assert not any(r['id_reserva'] == reserva.id_reserva for r in reservas_despues_de_cancelar) 