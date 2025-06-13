import pytest
import sys
import os
from sqlmodel import Session, select
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import BackgroundTasks
from unittest.mock import MagicMock, patch
import threading

# Add project root to the path to allow direct imports of app modules
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, root_dir)

# Adjust imports to bring in the service and models
from app.modules.reservations.services import (
    listar_reservas_usuario_comunidad_semana, 
    obtener_fechas_presenciales, 
    obtener_horas_presenciales, 
    listar_sesiones_presenciales_detalladas,
    crear_reserva_presencial
)
from app.modules.users.models import Usuario, Cliente
from app.modules.billing.models import Plan, Inscripcion, DetalleInscripcion
from app.modules.communities.models import Comunidad
from app.modules.services.models import Servicio, Local, Profesional
from app.modules.reservations.models import Reserva, Sesion, SesionPresencial

# --- Test Data ---
# It's good practice to keep test data separate and clear.
USER_A_DATA = {
    "nombre": "Concurrency", "apellido": "UserA", "email": "concurrency-a@example.com", 
    "password": "password123", "tipo": "cliente", "num_doc": "87654321",
    "id_departamento": 14, "id_distrito": 1, "tipo_documento": "DNI",
    "numero_telefono": "987654321", "talla": 170, "peso": 70
}
USER_B_DATA = {
    "nombre": "Concurrency", "apellido": "UserB", "email": "concurrency-b@example.com",
    "password": "password123", "tipo": "cliente", "num_doc": "12345679",
    "id_departamento": 14, "id_distrito": 1, "tipo_documento": "DNI",
    "numero_telefono": "987654322", "talla": 180, "peso": 80
}

# --- Fixture for Test Setup and Teardown ---
@pytest.fixture(scope="function")
def setup_data_service_test(session_factory):
    """
    A fixture to set up all necessary data for the service-layer concurrency test.
    This version correctly manages the session to ensure it remains open for teardown.
    """
    session = session_factory()
    created_records = {
        "comunidad": None, "plan": None, "servicio": None, "local": None,
        "profesional": None, "sesion_base": None, "sesion_presencial": None,
        "users": [], "clients": [], "inscripciones": [], "detalles": []
    }

    try:
        # 1. Cleanup from any previous failed runs (more robustly)
        for user_data in [USER_A_DATA, USER_B_DATA]:
            user = session.exec(select(Usuario).where(Usuario.email == user_data["email"])).first()
            if user:
                # Manually cascade delete related records if they exist
                client = session.exec(select(Cliente).where(Cliente.id_usuario == user.id_usuario)).first()
                if client:
                    insc = session.exec(select(Inscripcion).where(Inscripcion.id_cliente == client.id_cliente)).first()
                    if insc:
                        det = session.exec(select(DetalleInscripcion).where(DetalleInscripcion.id_inscripcion == insc.id_inscripcion)).first()
                        if det:
                            session.delete(det)
                    session.delete(client)
                session.delete(user)
        session.commit()

        # 2. Create all test data, tracking created objects for teardown
        comunidad = Comunidad(nombre="Comunidad Concurrencia Servicio", slogan="Desc", creado_por="test")
        session.add(comunidad)
        session.commit()
        created_records["comunidad"] = comunidad

        plan = Plan(nombre="Plan Concurrencia", descripcion="Desc", precio=10.0, creado_por="test", tipo_plan="TOPES")
        session.add(plan)
        session.commit()
        created_records["plan"] = plan

        servicio = Servicio(nombre="Servicio Concurrencia", descripcion="Desc", creado_por="test", modalidad="Presencial", fecha_creacion=datetime.utcnow(), estado=1)
        session.add(servicio)
        session.commit()
        created_records["servicio"] = servicio

        local = Local(nombre="Local Concurrencia", direccion="Direccion", id_departamento=14, id_distrito=1, id_servicio=servicio.id_servicio)
        session.add(local)
        session.commit()
        created_records["local"] = local

        profesional = Profesional(nombre_completo="Profesional Concurrencia", id_servicio=servicio.id_servicio)
        session.add(profesional)
        session.commit()
        created_records["profesional"] = profesional

        sesion_base = Sesion(id_servicio=servicio.id_servicio, fecha_inicio=datetime.utcnow() + timedelta(days=1), vacantes=1, creado_por="test", descripcion="Test Session")
        session.add(sesion_base)
        session.commit()
        created_records["sesion_base"] = sesion_base

        sesion_presencial = SesionPresencial(id_sesion=sesion_base.id_sesion, id_local=local.id_local, id_profesional=profesional.id_profesional)
        session.add(sesion_presencial)
        session.commit()
        created_records["sesion_presencial"] = sesion_presencial

        user_ids = []
        for user_data in [USER_A_DATA, USER_B_DATA]:
            usuario = Usuario(nombre=user_data["nombre"], apellido=user_data["apellido"], email=user_data["email"], password=user_data["password"], tipo=user_data["tipo"], estado=True)
            session.add(usuario)
            session.commit()
            created_records["users"].append(usuario)
            
            cliente = Cliente(id_usuario=usuario.id_usuario, tipo_documento=user_data["tipo_documento"], num_doc=user_data["num_doc"], numero_telefono=user_data["numero_telefono"], id_departamento=user_data["id_departamento"], id_distrito=user_data["id_distrito"], talla=user_data["talla"], peso=user_data["peso"])
            session.add(cliente)
            session.commit()
            created_records["clients"].append(cliente)

            inscripcion = Inscripcion(id_plan=plan.id_plan, id_comunidad=comunidad.id_comunidad, id_cliente=cliente.id_cliente, creado_por="test", estado=1)
            session.add(inscripcion)
            session.commit()
            created_records["inscripciones"].append(inscripcion)

            detalle = DetalleInscripcion(id_inscripcion=inscripcion.id_inscripcion, topes_disponibles=5, topes_consumidos=0, creado_por="test", estado=1)
            session.add(detalle)
            session.commit()
            created_records["detalles"].append(detalle)
            
            user_ids.append(usuario.id_usuario)

        yield {"sesion_id": sesion_base.id_sesion, "user_a_id": user_ids[0], "user_b_id": user_ids[1]}

    finally:
        # Teardown logic runs here, with the session still open
        # Delete in reverse order of creation to respect foreign key constraints
        for record in reversed(created_records["detalles"]):
            session.delete(record)
        for record in reversed(created_records["inscripciones"]):
            session.delete(record)
        for record in reversed(created_records["clients"]):
            session.delete(record)
        for record in reversed(created_records["users"]):
            session.delete(record)
        
        if created_records["sesion_presencial"]:
            session.delete(created_records["sesion_presencial"])
        if created_records["sesion_base"]:
            session.delete(created_records["sesion_base"])
        if created_records["profesional"]:
            session.delete(created_records["profesional"])
        if created_records["local"]:
            session.delete(created_records["local"])
        if created_records["servicio"]:
            session.delete(created_records["servicio"])
        if created_records["plan"]:
            session.delete(created_records["plan"])
        if created_records["comunidad"]:
            session.delete(created_records["comunidad"])
            
        session.commit()
        session.close()

# --- Worker Function for Concurrency ---
def attempt_reservation_service(user_id, sesion_id, session_factory):
    """Helper function to be run in a thread, simulating one user's attempt."""
    print(f"\n[THREAD {user_id}] Starting.")
    with session_factory() as db:
        try:
            # We pass the user ID directly to the service function
            reserva, error = crear_reserva_presencial(db=db, id_sesion=sesion_id, id_usuario=user_id)
            if error:
                print(f"[THREAD {user_id}] Service returned error: {error}")
                return "ERROR", error
            print(f"[THREAD {user_id}] Service returned success.")
            return "SUCCESS", reserva
        except Exception as e:
            import traceback
            print(f"[THREAD {user_id}] Caught EXCEPTION: {e}")
            traceback.print_exc()
            return "EXCEPTION", str(e)

# --- The Actual Test Case ---
def test_concurrency_on_last_spot_service_layer(session_factory, setup_data_service_test):
    """
    Tests the concurrency handling of the `crear_reserva_presencial` service directly.
    Simulates two users trying to book the last spot at the same time.
    """
    sesion_id = setup_data_service_test["sesion_id"]
    user_a_id = setup_data_service_test["user_a_id"]
    user_b_id = setup_data_service_test["user_b_id"]

    raw_results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(attempt_reservation_service, user_a_id, sesion_id, session_factory)
        future_b = executor.submit(attempt_reservation_service, user_b_id, sesion_id, session_factory)

        for future in as_completed([future_a, future_b]):
            try:
                # result() re-raises exceptions from the thread
                result = future.result()
                raw_results.append(result)
            except Exception as exc:
                print(f"\nCaught exception from future.result(): {exc}")
                raw_results.append(("FUTURE_EXCEPTION", str(exc)))
    
    print(f"\nRaw results from threads: {raw_results}")

    # --- Assertions ---
    assert len(raw_results) == 2, "Expected results from both threads."

    # Unpack results for clarity
    success_results = [r[1] for r in raw_results if r[0] == "SUCCESS" and isinstance(r[1], Reserva)]
    error_results = [r[1] for r in raw_results if r[0] == "ERROR"]

    print(f"Success results: {success_results}")
    print(f"Error results: {error_results}")
    
    assert len(success_results) == 1, "Expected exactly one successful reservation."
    assert len(error_results) == 1, "Expected exactly one failed reservation."

    # Verify the error message for the failed attempt
    assert "No hay vacantes disponibles" in error_results[0][0]

    # Verify the database state after the dust settles
    with session_factory() as db:
        # Check that the vacancy is now 0
        final_sesion = db.get(Sesion, sesion_id)
        assert final_sesion.vacantes == 0, "Vacancy should be 0 after successful reservation."

        # Check that only one reservation was created
        reservas = db.exec(select(Reserva).where(Reserva.id_sesion == sesion_id)).all()
        assert len(reservas) == 1, "There should be exactly one reservation in the DB."
        