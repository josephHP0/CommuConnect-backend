import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os
from typing import AsyncGenerator

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.main import app
from app.core.db import get_session, engine
from app.modules.users.models import Usuario, Administrador
from app.modules.users.schemas import UsuarioCreate
from app.modules.users.services import crear_usuario
from app.core.enums import TipoUsuario
from app.modules.communities.models import Comunidad
from app.modules.services.models import Servicio, ComunidadXServicio
from sqlmodel import Session, select, delete
from datetime import datetime
import random

# Override the app's session dependency
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function") 
async def admin_token(async_client: AsyncClient) -> str:
    admin_email = "admin.servicios.test@test.com"
    admin_password = "adminpassword"
    
    for session in app.dependency_overrides[get_session]():
        existing_user = session.exec(select(Usuario).where(Usuario.email == admin_email)).first()

        if not existing_user:
            admin_user_data = UsuarioCreate(
                nombre="AdminServicios",
                apellido="Test",
                email=admin_email,
                password=admin_password,
                tipo=TipoUsuario.Administrador
            )
            new_user = crear_usuario(session, admin_user_data)
            session.refresh(new_user)
            
            admin_record = Administrador(id_usuario=new_user.id_usuario)
            session.add(admin_record)
            session.commit()
            session.refresh(new_user)
            session.refresh(admin_record)

        response = await async_client.post("/api/auth/login", json={
            "email": admin_email,
            "password": admin_password
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return token

@pytest.fixture(scope="function")
async def test_data():
    """Crea datos de prueba para los tests"""
    rand_id = random.randint(10000, 99999)
    
    for session in app.dependency_overrides[get_session]():
        # Crear comunidad de prueba
        comunidad = Comunidad(
            nombre=f"Comunidad Test {rand_id}",
            slogan="Slogan de prueba",
            estado=True,
            fecha_creacion=datetime.utcnow(),
            creado_por="test_admin"
        )
        session.add(comunidad)
        session.commit()
        session.refresh(comunidad)
        
        # Crear servicios de prueba
        servicio1 = Servicio(
            nombre=f"Yoga Test {rand_id}",
            descripcion="Servicio de yoga para tests",
            modalidad="Presencial",
            estado=True,
            fecha_creacion=datetime.utcnow(),
            creado_por="test_admin"
        )
        
        servicio2 = Servicio(
            nombre=f"Pilates Test {rand_id}",
            descripcion="Servicio de pilates para tests",
            modalidad="Virtual", 
            estado=True,
            fecha_creacion=datetime.utcnow(),
            creado_por="test_admin"
        )
        
        servicio3 = Servicio(
            nombre=f"Crossfit Test {rand_id}",
            descripcion="Servicio de crossfit para tests",
            modalidad="Presencial",
            estado=True,
            fecha_creacion=datetime.utcnow(),
            creado_por="test_admin"
        )
        
        session.add_all([servicio1, servicio2, servicio3])
        session.commit()
        session.refresh(servicio1)
        session.refresh(servicio2)
        session.refresh(servicio3)
        
        # Crear relación existente: comunidad ya tiene servicio1 activo
        relacion_activa = ComunidadXServicio(
            id_comunidad=comunidad.id_comunidad,
            id_servicio=servicio1.id_servicio,
            estado=1
        )
        
        # Crear relación desactivada: comunidad tenía servicio2 pero está desactivado
        relacion_inactiva = ComunidadXServicio(
            id_comunidad=comunidad.id_comunidad,
            id_servicio=servicio2.id_servicio,
            estado=0
        )
        
        session.add_all([relacion_activa, relacion_inactiva])
        session.commit()
        
        yield {
            "comunidad_id": comunidad.id_comunidad,
            "servicio1_id": servicio1.id_servicio,  # Ya asociado y activo
            "servicio2_id": servicio2.id_servicio,  # Asociado pero inactivo
            "servicio3_id": servicio3.id_servicio,  # No asociado
            "rand_id": rand_id
        }
        
        # Cleanup
        session.exec(delete(ComunidadXServicio).where(ComunidadXServicio.id_comunidad == comunidad.id_comunidad))
        session.exec(delete(Servicio).where(Servicio.id_servicio.in_([servicio1.id_servicio, servicio2.id_servicio, servicio3.id_servicio])))
        session.exec(delete(Comunidad).where(Comunidad.id_comunidad == comunidad.id_comunidad))
        session.commit()

@pytest.mark.asyncio
async def test_listar_servicios_por_comunidad_admin(admin_token: str, async_client: AsyncClient, test_data):
    """Test para listar servicios activos de una comunidad (admin)"""
    comunidad_id = test_data["comunidad_id"]
    
    response = await async_client.get(
        f"/api/services/admin/comunidad/{comunidad_id}/servicios",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    servicios = response.json()
    assert isinstance(servicios, list)
    assert len(servicios) == 1  # Solo el servicio1 está activo
    assert servicios[0]["id_servicio"] == test_data["servicio1_id"]

@pytest.mark.asyncio
async def test_listar_servicios_disponibles_para_comunidad(admin_token: str, async_client: AsyncClient, test_data):
    """Test para listar servicios disponibles para añadir a una comunidad"""
    comunidad_id = test_data["comunidad_id"]
    
    response = await async_client.get(
        f"/api/services/admin/comunidad/{comunidad_id}/servicios-disponibles",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    servicios_disponibles = response.json()
    assert isinstance(servicios_disponibles, list)
    assert len(servicios_disponibles) >= 2  # Al menos servicio2 (inactivo) y servicio3 (no asociado)
    
    # Verificar que están los servicios correctos
    ids_disponibles = {s["id_servicio"] for s in servicios_disponibles}
    assert test_data["servicio2_id"] in ids_disponibles  # Inactivo, debería aparecer
    assert test_data["servicio3_id"] in ids_disponibles  # No asociado, debería aparecer
    assert test_data["servicio1_id"] not in ids_disponibles  # Activo, NO debería aparecer

@pytest.mark.asyncio
async def test_añadir_servicio_nuevo_a_comunidad(admin_token: str, async_client: AsyncClient, test_data):
    """Test para añadir un servicio completamente nuevo a una comunidad"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio3_id"]  # Servicio no asociado
    
    response = await async_client.post(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/añadir",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "Servicio añadido exitosamente a la comunidad"
    assert data["accion"] == "creado"
    assert data["id_comunidad"] == comunidad_id
    assert data["id_servicio"] == servicio_id
    assert data["estado"] == 1

@pytest.mark.asyncio
async def test_reactivar_servicio_en_comunidad(admin_token: str, async_client: AsyncClient, test_data):
    """Test para reactivar un servicio que estaba desactivado"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio2_id"]  # Servicio inactivo
    
    response = await async_client.post(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/añadir",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "Servicio reactivado exitosamente en la comunidad"
    assert data["accion"] == "reactivado"
    assert data["id_comunidad"] == comunidad_id
    assert data["id_servicio"] == servicio_id
    assert data["estado"] == 1

@pytest.mark.asyncio
async def test_añadir_servicio_ya_activo(admin_token: str, async_client: AsyncClient, test_data):
    """Test para intentar añadir un servicio que ya está activo"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio1_id"]  # Servicio ya activo
    
    response = await async_client.post(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/añadir",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "El servicio ya está activo en esta comunidad"
    assert data["accion"] == "ya_existe"
    assert data["estado"] == 1

@pytest.mark.asyncio
async def test_cambiar_estado_servicio_a_inactivo(admin_token: str, async_client: AsyncClient, test_data):
    """Test para desactivar un servicio en una comunidad"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio1_id"]  # Servicio activo
    
    response = await async_client.patch(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/estado?estado=0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "Servicio desactivado exitosamente en la comunidad"
    assert data["estado_anterior"] == 1
    assert data["estado_nuevo"] == 0

@pytest.mark.asyncio
async def test_cambiar_estado_servicio_a_activo(admin_token: str, async_client: AsyncClient, test_data):
    """Test para activar un servicio en una comunidad"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio2_id"]  # Servicio inactivo
    
    response = await async_client.patch(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/estado?estado=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "Servicio activado exitosamente en la comunidad"
    assert data["estado_anterior"] == 0
    assert data["estado_nuevo"] == 1

@pytest.mark.asyncio
async def test_cambiar_estado_con_valor_invalido(admin_token: str, async_client: AsyncClient, test_data):
    """Test para validar que solo se acepten estados 0 o 1"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio1_id"]
    
    response = await async_client.patch(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/estado?estado=2",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 400
    assert "Estado debe ser 0 (inactivo) o 1 (activo)" in response.json()["detail"]

@pytest.mark.asyncio
async def test_operaciones_con_relacion_inexistente(admin_token: str, async_client: AsyncClient, test_data):
    """Test para manejar relaciones que no existen"""
    comunidad_id = test_data["comunidad_id"]
    servicio_inexistente = 99999
    
    # Intentar cambiar estado de relación inexistente
    response = await async_client.patch(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_inexistente}/estado?estado=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404
    assert "No existe relación" in response.json()["detail"]

@pytest.mark.asyncio 
async def test_operaciones_sin_permisos_admin(async_client: AsyncClient, test_data):
    """Test para verificar que solo admins pueden usar estos endpoints"""
    comunidad_id = test_data["comunidad_id"]
    servicio_id = test_data["servicio1_id"]
    
    # Sin token de autorización
    response = await async_client.get(f"/api/services/admin/comunidad/{comunidad_id}/servicios")
    assert response.status_code == 401
    
    # Cambiar estado sin autorización
    response = await async_client.patch(
        f"/api/services/admin/comunidad/{comunidad_id}/servicio/{servicio_id}/estado?estado=0"
    )
    assert response.status_code == 401 
