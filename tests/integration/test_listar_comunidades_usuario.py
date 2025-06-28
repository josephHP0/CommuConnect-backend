import sys
import os
from fastapi.testclient import TestClient
import json


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
    "email": "mr@cc.com",
    "password": "1234"
}


def test_login_y_comunidades():
    # Paso 1: Intentar login
    response_login = client.post("/api/auth/login", json=LOGIN_DATA)

    if response_login.status_code != 200:
        print(" Error en el login:")
        print(f"- Código de estado: {response_login.status_code}")
        print(f"- Respuesta: {response_login.text}")
        assert False, "Fallo en el paso de login"

    token = response_login.json().get("access_token")
    if not token:
        print("Token no encontrado en la respuesta del login.")
        print(f"- Respuesta: {response_login.json()}")
        assert False, "No se obtuvo el token"

    headers = {"Authorization": f"Bearer {token}"}

    # Paso 2: Intentar obtener comunidades del usuario
    response = client.get("/api/usuarios/usuario/comunidades", headers=headers)

    if response.status_code != 200:
        print("\nERROR AL OBTENER COMUNIDADES DEL USUARIO")
        print(f"- Código HTTP: {response.status_code}")
        print(f"- Ruta usada: /api/usuarios/usuario/comunidades")
        try:
            print(f"- Detalle del error: {response.json()}")
        except Exception:
            print(f"- Respuesta cruda (text): {response.text}")
        
        # Lanzar fallo después de mostrar todo
        assert False, "Fallo en el paso de obtención de comunidades"


    comunidades = response.json()
    print("\nComunidades obtenidas correctamente:")
    for c in comunidades:
        servicios = [s['nombre'] for s in c.get('servicios', [])]
        print(f"- {c.get('nombre')} con servicios: {servicios}")
    print("\n JSON crudo recibido:")
    print(json.dumps(comunidades, indent=2))


if __name__ == "__main__":
    test_login_y_comunidades()
