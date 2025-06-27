import pytest
import pandas as pd
from io import BytesIO
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def create_test_excel_locales():
    """Crea un archivo Excel de prueba con la estructura esperada para locales"""
    data = {
        'nombre': [
            'Local Centro Lima',
            'Local San Isidro',
            'Local Miraflores',
            'Local Surco'
        ],
        'id_distrito': [1, 2, 3, 4],  # Diferentes distritos (departamento será 14 por defecto)
        'direccion_detallada': [
            'Av. Javier Prado 123, Centro de Lima',
            'Av. Camino Real 456, San Isidro',
            'Av. Larco 789, Miraflores',
            'Av. Primavera 321, Santiago de Surco'
        ],
        'responsable': [
            'Juan Pérez',
            'María García',
            None,  # Sin responsable para mostrar que es opcional
            'Ana Torres'
        ],
        'link': [
            'https://maps.google.com/centro-lima',
            'https://maps.google.com/san-isidro',
            'https://maps.google.com/miraflores',
            'https://maps.google.com/surco'
        ]
    }
    
    df = pd.DataFrame(data)
    
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    return excel_buffer

def create_test_excel_locales_invalid():
    """Crea un archivo Excel de prueba con datos inválidos"""
    data = {
        'nombre': [
            '',  # Nombre vacío (inválido)
            'Local Válido',
            'Local Sin Distrito',
            'Local Sin Dirección'
        ],
        'id_distrito': [1, 2, None, 4],  # Algunos nulos (departamento será 14 por defecto)
        'direccion_detallada': [
            'Dirección test',
            'Av. Test 123',
            'Av. Test 456',
            ''  # Dirección vacía (inválido)
        ],
        'responsable': [
            'Responsable Test',
            'María García',
            'Carlos López',
            'Ana Torres'
        ],
        'link': [
            'https://test.com',
            'https://maps.google.com/test',
            'https://maps.google.com/test2',
            'https://maps.google.com/test3'
        ]
    }
    
    df = pd.DataFrame(data)
    
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    return excel_buffer

def test_estructura_excel_locales():
    """Prueba que podemos crear un Excel con la estructura correcta para locales"""
    excel_file = create_test_excel_locales()
    
    # Verificar que el buffer no está vacío
    assert excel_file.getvalue(), "El archivo Excel no debería estar vacío"
    
    # Leer el Excel para verificar estructura
    df = pd.read_excel(excel_file)
    print("\n📊 Estructura del Excel de prueba para locales:")
    print(df.head())
    print(f"\n📋 Columnas: {list(df.columns)}")
    print(f"📊 Filas: {len(df)}")
    
    # Verificar columnas esperadas
    columnas_esperadas = ['nombre', 'id_distrito', 'direccion_detallada', 'responsable', 'link']
    for col in columnas_esperadas:
        assert col in df.columns, f"Falta la columna {col}"
    
    # Verificar que hay datos
    assert len(df) > 0, "Debe haber al menos una fila de datos"
    
    print("✅ Estructura del Excel para locales validada correctamente")

def test_carga_masiva_locales_validos():
    """Prueba la carga masiva de locales con datos válidos"""
    # Este test requiere un servicio existente y autenticación de ADMINISTRADOR
    # Se puede ejecutar manualmente con un token válido de admin
    
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    ID_SERVICIO = 1  # Cambiar por un ID de servicio válido
    
    # Crear archivo Excel de prueba
    excel_file = create_test_excel_locales()
    
    # Headers de autenticación (requiere token de ADMINISTRADOR)
    headers = {
        # "Authorization": "Bearer <TOKEN_ADMIN_AQUI>"
    }
    
    files = {"archivo": ("test_locales.xlsx", excel_file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    
    print("📤 Enviando archivo Excel con locales válidos...")
    print(f"🎯 URL: {BASE_URL}/services/locales/carga-masiva/{ID_SERVICIO}")
    print("⚠️  Nota: Este test requiere token de ADMINISTRADOR. Descomenta y agrega el token en headers.")
    
    # Descomentar para ejecutar con token válido:
    # response = requests.post(
    #     f"{BASE_URL}/services/locales/carga-masiva/{ID_SERVICIO}",
    #     files=files,
    #     headers=headers
    # )
    # 
    # print(f"📊 Status Code: {response.status_code}")
    # print(f"📄 Response: {response.json()}")
    # 
    # assert response.status_code == 200
    # data = response.json()
    # assert "mensaje" in data
    # assert "resumen" in data
    # assert data["resumen"]["insertados"] > 0

def test_carga_masiva_locales_invalidos():
    """Prueba la carga masiva con datos inválidos"""
    # Similar al test anterior pero con datos inválidos
    
    excel_file = create_test_excel_locales_invalid()
    
    print("📤 Enviando archivo Excel con locales inválidos...")
    print("⚠️  Nota: Este test requiere token de ADMINISTRADOR. Los datos inválidos deberían ser omitidos o generar errores.")
    
    # El archivo se crea correctamente, pero algunos registros serán omitidos
    # debido a datos faltantes o inválidos

if __name__ == "__main__":
    print("🧪 Ejecutando pruebas de carga masiva de locales...")
    print("=" * 50)
    
    # Ejecutar pruebas básicas
    test_estructura_excel_locales()
    test_carga_masiva_locales_validos()
    test_carga_masiva_locales_invalidos()
    
    print("\n✅ Pruebas completadas!")
    print("\n📝 Para usar el endpoint:")
    print("1. Obtén un token de ADMINISTRADOR")
    print("2. Crea un Excel con las columnas: nombre, id_distrito, direccion_detallada, responsable, link")
    print("   - nombre, id_distrito, direccion_detallada son OBLIGATORIOS")
    print("   - responsable y link son OPCIONALES")
    print("3. Envía POST a /services/locales/carga-masiva/{id_servicio}")
    print("4. Incluye el archivo en el campo 'archivo' y el token de admin en Authorization header")
    print("📍 NOTA: El departamento se asigna automáticamente como 14 (por defecto)")
    print("⚠️  IMPORTANTE: Solo usuarios con permisos de administrador pueden usar este endpoint") 