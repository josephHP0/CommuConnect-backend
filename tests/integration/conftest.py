import sys
import os
import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from fastapi.testclient import TestClient

# 1) Insertamos manualmente la ruta del proyecto (donde está app/)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 2) Ahora sí podemos importar normal:
from app.main import app
from app.core.db import get_session as get_session_real, DATABASE_URL

# Si tu engine (en app/core/db.py) está creado así:
# engine = create_engine(DATABASE_URL)
# podrías hacer aquí algo similar:
engine = create_engine(DATABASE_URL)

@pytest.fixture(name="session_test")
def session_fixture():
    """
    En lugar de crear tablas nuevas, simplemente abrimos una sesión 
    apuntando a tu base de datos real. 
    ADVERTENCIA: Esto hará cambios en tu BD existente.
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        # NO hacemos drop_all ni create_all aquí, porque queremos usar la BD "tal cual existe".

@pytest.fixture(name="client")
def client_fixture(session_test: Session):
    def get_session_override():
        try:
            yield session_test
        finally:
            pass

    app.dependency_overrides[get_session_real] = get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user_token(client: TestClient, session_test: Session) -> str:
    from app.modules.users.models import Usuario, Cliente
    from app.modules.reservations.models import Reserva
    from app.modules.billing.models import Inscripcion, DetalleInscripcion

    test_user_data = {
        "nombre": "Test",
        "apellido": "User",
        "email": "jitojif852@adrewire.com",
        "password": "testpassword",
        "tipo_documento": "DNI",
        "num_doc": "12345678",
        "numero_telefono": "987654321",
        "id_departamento": 14,
        "id_distrito": 1,
        "talla": 170,
        "peso": 70
    }
    
    existing_cliente_by_doc = session_test.exec(
        select(Cliente).where(Cliente.num_doc == test_user_data["num_doc"])
    ).first()
    if existing_cliente_by_doc:
        reservas = session_test.exec(select(Reserva).where(Reserva.id_cliente == existing_cliente_by_doc.id_cliente)).all()
        for r in reservas:
            session_test.delete(r)
        
        inscripciones = session_test.exec(select(Inscripcion).where(Inscripcion.id_cliente == existing_cliente_by_doc.id_cliente)).all()
        for i in inscripciones:
             detalles = session_test.exec(select(DetalleInscripcion).where(DetalleInscripcion.id_inscripcion == i.id_inscripcion)).all()
             for d in detalles:
                 session_test.delete(d)
             session_test.delete(i)

        user_to_delete = session_test.get(Usuario, existing_cliente_by_doc.id_usuario)
        session_test.delete(existing_cliente_by_doc)
        if user_to_delete:
            session_test.delete(user_to_delete)
        session_test.commit()

    user_existing = session_test.exec(select(Usuario).where(Usuario.email == test_user_data["email"])).first()
    if user_existing:
        cliente_existing = session_test.exec(select(Cliente).where(Cliente.id_usuario == user_existing.id_usuario)).first()
        if cliente_existing:
            session_test.delete(cliente_existing)
        session_test.delete(user_existing)
        session_test.commit()

    response = client.post("/api/usuarios/cliente", json=test_user_data)
    assert response.status_code == 200, f"Failed to create client: {response.text}"

    user_db = session_test.exec(select(Usuario).where(Usuario.email == test_user_data["email"])).first()
    assert user_db, "User not found in DB after creation"
    user_db.estado = True
    session_test.add(user_db)
    session_test.commit()
    session_test.refresh(user_db)

    login_data = {"email": test_user_data["email"], "password": test_user_data["password"]}
    token_response = client.post("/api/auth/login", json=login_data)
    assert token_response.status_code == 200, f"Failed to get token: {token_response.text}"
    token = token_response.json()["access_token"]
    return token