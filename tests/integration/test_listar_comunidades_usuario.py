import sys
import os
import json
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder

# Agregar la base del proyecto al sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importar la aplicación principal
from app.main import app

# Crear cliente de pruebas
client = TestClient(app)

# Credenciales de un usuario que ya debe existir en la base de datos
LOGIN_DATA = {
    "email": "lr@cc.com",
    "password": "1234"
}


def test_login_y_comunidades():
    # Paso 1: Login
    response_login = client.post("/api/auth/login", json=LOGIN_DATA)

    if response_login.status_code != 200:
        print("❌ Error en el login:")
        print(f"- Código de estado: {response_login.status_code}")
        print(f"- Respuesta: {response_login.text}")
        assert False, "Fallo en el paso de login"

    token = response_login.json().get("access_token")
    if not token:
        print("❌ Token no encontrado en la respuesta del login.")
        print(f"- Respuesta: {response_login.json()}")
        assert False, "No se obtuvo el token"

    headers = {"Authorization": f"Bearer {token}"}

    # Paso 2: Obtener comunidades del usuario
    response = client.get("/api/usuarios/usuario/comunidades", headers=headers)

    if response.status_code != 200:
        print("\n❌ ERROR AL OBTENER COMUNIDADES DEL USUARIO")
        print(f"- Código HTTP: {response.status_code}")
        print(f"- Ruta usada: /api/usuarios/usuario/comunidades")
        try:
            print(f"- Detalle del error: {response.json()}")
        except Exception:
            print(f"- Respuesta cruda (text): {response.text}")
        assert False, "Fallo en el paso de obtención de comunidades"

    comunidades = response.json()

    # ✅ Validaciones estructurales mínimas
    for comunidad in comunidades:
        assert "estado_membresia" in comunidad, "Falta 'estado_membresia' en la respuesta"
        assert "estado_inscripcion" in comunidad, "Falta 'estado_inscripcion' en la respuesta"
        assert isinstance(comunidad["estado_inscripcion"], int) or comunidad["estado_inscripcion"] is None, "'estado_inscripcion' debe ser int o None"

    # 🟢 Imprimir resumen
    print("\n✅ Comunidades obtenidas correctamente:")
    for c in comunidades:
        servicios = [s['nombre'] for s in c.get('servicios', [])]
        print(f"- {c.get('nombre')} (servicios: {servicios})")

    # 🟡 Imprimir JSON completo
    print("\n📦 JSON crudo recibido:")
    print(json.dumps(comunidades, indent=2))


if __name__ == "__main__":
    test_login_y_comunidades()
