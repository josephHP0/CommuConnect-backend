import sys
import os
import pytest
from sqlmodel import SQLModel, create_engine, Session
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
        # NO hacemos drop_all ni create_all aquí, porque queremos usar la BD “tal cual existe”.

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