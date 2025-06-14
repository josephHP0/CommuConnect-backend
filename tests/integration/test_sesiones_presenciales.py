import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.modules.users.models import Usuario, Cliente
from app.modules.communities.models import Comunidad
from app.modules.services.models import Servicio, Local, ComunidadXServicio, Profesional
from app.modules.reservations.models import Sesion, SesionPresencial
from utils.datetime_utils import convert_local_to_utc

def test_listar_sesiones_presenciales(client: TestClient, session_test: Session, test_user_token: str):
    # 1. Setup: Crear datos de prueba
    comunidad = Comunidad(nombre="Comunidad Sesiones P", slogan="Test", creado_por="test")
    servicio = Servicio(nombre="Servicio Sesiones P", descripcion="Test", creado_por="test", modalidad="Presencial", fecha_creacion=datetime.utcnow(), estado=1)
    local = Local(nombre="Local Sesiones P", direccion_detallada="Av. Ficticia 456", responsable="Carlos Santana", id_departamento=14, id_distrito=1)
    
    session_test.add_all([comunidad, servicio, local])
    session_test.commit()
    session_test.refresh(comunidad); session_test.refresh(servicio); session_test.refresh(local)

    local.id_servicio = servicio.id_servicio
    comunidad_x_servicio = ComunidadXServicio(id_comunidad=comunidad.id_comunidad, id_servicio=servicio.id_servicio)
    session_test.add(comunidad_x_servicio)

    # Crear una sesión en una hora UTC específica
    # Por ejemplo, 22:00 UTC, que son las 5 PM en Lima
    fecha_sesion_utc = datetime.utcnow().replace(hour=22, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    sesion = Sesion(id_servicio=servicio.id_servicio, descripcion="Sesión de prueba presencial", inicio=fecha_sesion_utc, fin=fecha_sesion_utc + timedelta(hours=1), tipo="Presencial")
    session_test.add(sesion)
    session_test.commit()
    session_test.refresh(sesion)
    
    sesion_presencial = SesionPresencial(id_sesion=sesion.id_sesion, id_local=local.id_local, capacidad=15)
    session_test.add(sesion_presencial)
    session_test.commit()

    # 2. Simular la llamada del frontend (con hora local de Lima)
    # El usuario en Perú ve las 5 PM y envía "17:00"
    hora_local_lima = "17:00"
    fecha_local_lima = (fecha_sesion_utc.date()).strftime("%d/%m/%Y")

    response = client.get(
        f"/api/reservations/sesiones-presenciales?id_servicio={servicio.id_servicio}&id_distrito={local.id_distrito}&id_local={local.id_local}&fecha={fecha_local_lima}&hora={hora_local_lima}"
    )

    # 3. Assertions
    assert response.status_code == 200, response.text
    data = response.json()
    
    assert "sesiones" in data
    assert len(data["sesiones"]) == 1
    
    sesion_resp = data["sesiones"][0]
    assert sesion_resp["id_sesion"] == sesion.id_sesion
    assert sesion_resp["ubicacion"] == local.nombre
    assert sesion_resp["responsable"] == local.responsable
    
    # Verificar que la hora devuelta también está en formato local de Lima (17:00)
    assert sesion_resp["hora_inicio"] == "17:00"
