import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.modules.users.models import Usuario, Cliente
from app.modules.communities.models import Comunidad
from app.modules.services.models import Servicio, Local, ComunidadXServicio
from app.modules.reservations.models import Sesion, SesionPresencial, Reserva
from app.modules.billing.models import Plan, Inscripcion, DetalleInscripcion

def test_full_reservation_flow(client: TestClient, session_test: Session, test_user_token: str):
    # 1. Setup
    user = session_test.exec(select(Usuario).where(Usuario.email == "jitojif852@adrewire.com")).one()
    cliente = session_test.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).one()

    # Define test data locally within the test or move to a shared location if needed by multiple tests
    test_community_data = {"nombre": "Comunidad de Prueba Flow", "slogan": "Desc", "creado_por": "test"}
    test_service_data = {"nombre": "Servicio de Prueba Flow", "descripcion": "Desc", "creado_por": "test", "modalidad": "Presencial", "estado": 1, "fecha_creacion": datetime.now()}
    test_local_data = {
        "nombre": "Local de Prueba Flow", "direccion_detallada": "Dir", 
        "id_departamento": 14, "id_distrito": 1, 
        "creado_por": "test"
    }
    test_plan_data = {
        "titulo": "Plan de Prueba Flow", "descripcion": "Desc", "topes": 5,
        "precio": 10.0, "creado_por": "test", "estado": 1
    }
    test_session_data = {
        "descripcion": "Sesión de prueba",
        "inicio": datetime.now() + timedelta(days=1),
        "fin": datetime.now() + timedelta(days=1, hours=1),
        "tipo": "Presencial", "creado_por": "test", "estado": 1
    }

    comunidad = Comunidad(**test_community_data)
    session_test.add(comunidad)

    servicio = Servicio(**test_service_data)
    session_test.add(servicio)

    session_test.commit()
    session_test.refresh(comunidad)
    session_test.refresh(servicio)

    comunidad_x_servicio = ComunidadXServicio(
        id_comunidad=comunidad.id_comunidad,
        id_servicio=servicio.id_servicio
    )
    session_test.add(comunidad_x_servicio)

    local_data = test_local_data.copy()
    local_data["id_servicio"] = servicio.id_servicio
    local = Local(**local_data)
    session_test.add(local)

    plan_data = test_plan_data.copy()
    plan_data["fecha_creacion"] = datetime.now()
    plan = Plan(**plan_data)
    session_test.add(plan)

    session_test.commit()
    session_test.refresh(local)
    session_test.refresh(plan)

    sesion = Sesion(id_servicio=servicio.id_servicio, **test_session_data)
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)

    sesion_presencial = SesionPresencial(
        id_sesion=sesion.id_sesion,
        id_local=local.id_local,
        capacidad=10,
        creado_por="test"
    )
    session_test.add(sesion_presencial)
    session_test.commit()
    session_test.refresh(sesion_presencial)

    inscripcion = Inscripcion(
        id_plan=plan.id_plan,
        id_comunidad=comunidad.id_comunidad,
        id_cliente=cliente.id_cliente,
        creado_por="test",
        estado=1
    )
    session_test.add(inscripcion)
    session_test.commit()
    session_test.refresh(inscripcion)

    detalle_inscripcion = DetalleInscripcion(
        id_inscripcion=inscripcion.id_inscripcion,
        topes_disponibles=plan.topes,
        topes_consumidos=0,
        creado_por="test",
        estado=1
    )
    session_test.add(detalle_inscripcion)
    session_test.commit()
    session_test.refresh(detalle_inscripcion)

    headers = {"Authorization": f"Bearer {test_user_token}"}

    summary_response = client.get(f"/api/reservations/summary/{sesion.id_sesion}", headers=headers)
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    assert summary_data["id_sesion"] == sesion.id_sesion
    assert summary_data["nombres"] == user.nombre
    assert summary_data["apellidos"] == user.apellido

    reserve_payload = {"id_sesion": sesion.id_sesion}
    reserve_response = client.post("/api/reservations/", json=reserve_payload, headers=headers)

    assert reserve_response.status_code == 201, f"Failed to reserve: {reserve_response.text}"
    reserve_data = reserve_response.json()
    assert reserve_data["id_reserva"] is not None
    assert reserve_data["nombre_servicio"] == servicio.nombre
    assert reserve_data["ubicacion"] == local.nombre
    assert reserve_data["nombre_cliente"] == user.nombre
    assert reserve_data["direccion_detallada"] == local.direccion_detallada
    assert reserve_data["topes_consumidos"] == 1
    assert reserve_data["topes_disponibles"] == test_plan_data["topes"]

    detalle_updated = session_test.get(DetalleInscripcion, detalle_inscripcion.id_registros_inscripcion)
    assert detalle_updated.topes_consumidos == 1

    reserva = session_test.get(Reserva, reserve_data["id_reserva"])
    session_test.delete(reserva)
    
    detalle_updated.topes_consumidos = 0
    session_test.add(detalle_updated)

    session_test.commit()