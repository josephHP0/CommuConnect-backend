import pytest
import pandas as pd
from io import BytesIO
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_carga_sesiones_presenciales_estructura_valida():
    """
    Test con estructura válida de Excel para sesiones presenciales.
    
    IMPORTANTE: Necesitas un token de ADMINISTRADOR válido para que funcione.
    Reemplaza 'TU_TOKEN_ADMIN_AQUI' con un token real.
    """
    
    # Datos de ejemplo para sesiones presenciales
    data = {
        'id_local': [1, 2, 1],  # Asegúrate de que estos locales existan
        'fecha_inicio': ['15/03/2025 09:00', '16/03/2025 14:00', '17/03/2025 18:00'],
        'fecha_fin': ['15/03/2025 10:00', '16/03/2025 15:30', '17/03/2025 19:00'],
        'capacidad': [20, 15, None],  # Última sin capacidad para probar opcional
        'descripcion': ['Yoga Matutino', 'Pilates Avanzado', None]  # Última sin descripción para probar opcional
    }
    
    # Crear DataFrame y convertir a Excel
    df = pd.DataFrame(data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    # Headers con token de administrador
    headers = {
        "Authorization": "Bearer TU_TOKEN_ADMIN_AQUI"  # REEMPLAZAR CON TOKEN REAL
    }
    
    # Realizar la petición
    response = client.post(
        "/services/sesiones-presenciales/carga-masiva/1",  # ID del servicio
        headers=headers,
        files={"archivo": ("sesiones_presenciales.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    
    # Validaciones
    assert response.status_code == 200
    data = response.json()
    assert "resultado" in data
    assert "insertados" in data["resultado"]
    assert "omitidos" in data["resultado"]
    assert "errores" in data["resultado"]

def test_carga_sesiones_presenciales_estructura_invalida():
    """
    Test con estructura inválida (falta columna obligatoria).
    """
    
    # Datos sin la columna 'fecha_inicio' (obligatoria)
    data = {
        'id_local': [1],
        'fecha_fin': ['15/03/2025 10:00']
        # Falta 'fecha_inicio'
    }
    
    df = pd.DataFrame(data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    headers = {
        "Authorization": "Bearer TU_TOKEN_ADMIN_AQUI"  # REEMPLAZAR CON TOKEN REAL
    }
    
    response = client.post(
        "/services/sesiones-presenciales/carga-masiva/1",
        headers=headers,
        files={"archivo": ("sesiones_invalidas.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    
    # Debería fallar por estructura inválida o procesar con errores
    assert response.status_code in [200, 400, 422]

def test_archivo_no_excel():
    """
    Test enviando un archivo que no es Excel.
    """
    headers = {
        "Authorization": "Bearer TU_TOKEN_ADMIN_AQUI"  # REEMPLAZAR CON TOKEN REAL
    }
    
    response = client.post(
        "/services/sesiones-presenciales/carga-masiva/1",
        headers=headers,
        files={"archivo": ("test.txt", b"contenido texto", "text/plain")}
    )
    
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    
    assert response.status_code == 400
    assert "Excel válido" in response.json()["detail"]

def generar_excel_ejemplo():
    """
    Función auxiliar para generar un archivo Excel de ejemplo.
    Útil para testing manual.
    """
    data = {
        'id_local': [1, 2, 3, 1, 2],  # Asegúrate de que estos IDs existan
        'fecha_inicio': [
            '20/03/2025 08:00',
            '20/03/2025 10:00',
            '20/03/2025 17:00',
            '21/03/2025 07:00',
            '21/03/2025 16:00'
        ],
        'fecha_fin': [
            '20/03/2025 09:00',
            '20/03/2025 11:30',
            '20/03/2025 18:00',
            '21/03/2025 08:00',
            '21/03/2025 17:00'
        ],
        'capacidad': [20, 15, None, 25, None],  # Algunas sin capacidad para mostrar que es opcional
        'descripcion': [
            'Yoga Matutino - Principiantes',
            'Pilates Avanzado',
            None,  # Sin descripción para mostrar que es opcional
            'Entrenamiento Funcional',
            None   # Sin descripción para mostrar que es opcional
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_excel('ejemplo_sesiones_presenciales.xlsx', index=False, engine='openpyxl')
    print("Archivo 'ejemplo_sesiones_presenciales.xlsx' generado exitosamente!")
    print("\nEstructura del archivo:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    print("=== GENERANDO ARCHIVO DE EJEMPLO ===")
    generar_excel_ejemplo()
    
    print("\n=== INSTRUCCIONES DE USO ===")
    print("1. Asegúrate de tener un token de administrador válido")
    print("2. Reemplaza 'TU_TOKEN_ADMIN_AQUI' en los tests con tu token real")
    print("3. Verifica que los IDs de locales en el ejemplo existan en tu base de datos")
    print("4. Ejecuta los tests con: pytest tests/integration/test_carga_sesiones_presenciales.py -v")
    print("\n=== ESTRUCTURA REQUERIDA DEL EXCEL ===")
    print("Columnas en este orden exacto:")
    print("1. id_local (obligatorio, debe existir en la BD)")
    print("2. fecha_inicio (obligatorio, formato: DD/MM/YYYY HH:MM)")
    print("3. fecha_fin (obligatorio, formato: DD/MM/YYYY HH:MM)")
    print("4. capacidad (opcional, número entero)")
    print("5. descripcion (opcional, si se omite se usará 'Sesión presencial')") 