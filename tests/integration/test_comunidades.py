import sys
import os
import io
import uuid
# para importar app correctamente
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)  # Esta línea es clave

# 1. Crear al admin (si no existe)
def test_crear_admin_si_no_existe():
    correo_unico = f"admin_{uuid.uuid4().hex[:6]}@demo.com"
    payload = {
        "nombre": "Super",
        "apellido": "Admin",
        "email": correo_unico,
        "password": "admin123"
    }
    response = client.post("/api/usuarios/administrador", json=payload)
    print("Crear admin:", response.status_code, response.json())
    assert response.status_code in (200, 201)

# 2. Obtener token JWT válido del admin
def obtener_token_admin():
    response = client.post("/api/auth/login", json={
        "email": "admin@prueba.com",
        "password": "admin123"
    })

    print("LOGIN:", response.status_code, response.json())
    assert response.status_code == 200, "❌ Login fallido"
    data = response.json()
    assert "access_token" in data, f"❌ Token no recibido: {data}"
    return data["access_token"]

# 3. Crear comunidad con imagen
def test_crear_comunidad_con_imagen():
    token = obtener_token_admin()
    imagen_dummy = io.BytesIO(b"contenido_simulado")

    response = client.post(
        "/api/comunidades/crear_comunidad",
        files={
            "nombre": (None, "Comunidad Salud Integral"),
            "slogan": (None, "Juntos por el bienestar"),
            "imagen": ("imagen.png", imagen_dummy, "image/png")
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["nombre"] == "Comunidad Salud Integral"
    assert data["imagen"] is not None

# 4. Crear comunidad sin imagen
def test_crear_comunidad_sin_imagen():
    token = obtener_token_admin()

    response = client.post(
        "/api/comunidades/crear_comunidad",
        files={
            "nombre": (None, "Comunidad sin Imagen"),
            "slogan": (None, "Solo texto por ahora")
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["nombre"] == "Comunidad sin Imagen"
    assert data["imagen"] is None

# 5. Listar todas las comunidades activas
def test_listar_comunidades():
    response = client.get("/api/comunidades/listar_comunidad")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "nombre" in data[0]
        assert "estado" in data[0]
