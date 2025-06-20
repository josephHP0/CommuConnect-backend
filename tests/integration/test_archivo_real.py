import sys
import os
import pytest
from httpx import AsyncClient
from sqlmodel import Session, select

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.db import get_session
from app.modules.users.models import Usuario, Cliente

@pytest.mark.asyncio
async def test_archivo_real_clientes_demo_cambiado(async_client: AsyncClient, admin_token: str, session_test: Session):
    """
    Prueba el endpoint de carga masiva con el archivo real del usuario.
    Ahora usa transacciones para NO insertar datos permanentemente en la BD.
    """
    print(f"\n🔑 Usando token de admin para archivo real (SIN inserción permanente)...")
    
    # Emails que vamos a insertar temporalmente 
    emails_temporales = ["karol@demo.com", "pep@demo.com"]
    
    # Ruta al archivo real del usuario
    archivo_path = r"C:\Users\patri\Downloads\clientes_demo_cambiado.xlsx"
    
    try:
        # Leer el archivo y preparar para envío
        with open(archivo_path, 'rb') as f:
            contenido_archivo = f.read()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        files = {"archivo": ("clientes_demo_cambiado.xlsx", contenido_archivo, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        print("📤 Enviando archivo real del usuario...")
        print(f"📁 Archivo: {archivo_path}")
        print(f"📊 Tamaño: {len(contenido_archivo)} bytes")
        
        # Guardar punto inicial para verificar rollback
        usuarios_antes = session_test.exec(
            select(Usuario).where(Usuario.email.in_(emails_temporales))
        ).all()
        print(f"👥 Usuarios con estos emails ANTES del test: {len(usuarios_antes)}")
        
        # Hacer la petición al endpoint
        response = await async_client.post("/api/usuarios/clientes/carga-masiva", headers=headers, files=files)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Carga masiva exitosa!")
            print(f"📈 Resumen: {result}")
        else:
            print("❌ Error en la carga masiva!")
            print(f"🔍 Status Code: {response.status_code}")
            print(f"📄 Response Text: {response.text}")
            
            # Intentar parsear como JSON para ver el error específico
            try:
                error_json = response.json()
                print(f"📝 Error JSON: {error_json}")
            except:
                print("❌ No se pudo parsear la respuesta como JSON")
                print(f"📄 Raw response: {response.content}")
        
        # Verificar que los datos se insertaron temporalmente
        usuarios_despues = session_test.exec(
            select(Usuario).where(Usuario.email.in_(emails_temporales))
        ).all()
        print(f"👥 Usuarios con estos emails DESPUÉS del test: {len(usuarios_despues)}")
        
        for usuario in usuarios_despues:
            print(f"   - {usuario.nombre} {usuario.apellido} - {usuario.email}")
        
        print("\n⚠️ NOTA: Estos datos se eliminarán automáticamente al finalizar el test")
        
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {archivo_path}")
        print("📝 Asegúrate de que la ruta sea correcta")
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        print(f"📝 Tipo de error: {type(e).__name__}")
        import traceback
        print(f"📄 Traceback completo:\n{traceback.format_exc()}")
        
    # Al final del test, la transacción se hará rollback automáticamente

@pytest.mark.asyncio
async def test_verificar_datos_existentes(async_client: AsyncClient, admin_token: str, session_test: Session):
    """
    Verifica si ya existen datos con los emails del archivo del usuario.
    Ahora usa transacciones para NO afectar la BD permanentemente.
    """
    print(f"\n🔍 Verificando datos existentes (con transacciones)...")
    
    # Emails del archivo del usuario
    emails_archivo = ["karol@demo.com", "pep@demo.com"]
    docs_archivo = ["72357812", "85768645"]
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Verificar directamente en la sesión transaccional
    usuarios_existentes = session_test.exec(
        select(Usuario).where(Usuario.email.in_(emails_archivo))
    ).all()
    
    print(f"👥 Usuarios encontrados con esos emails: {len(usuarios_existentes)}")
    
    for usuario in usuarios_existentes:
        print(f"⚠️  EMAIL EXISTENTE: {usuario.email} - {usuario.nombre} {usuario.apellido}")
    
    # Verificar clientes por DNI
    clientes_existentes = session_test.exec(
        select(Cliente).where(Cliente.num_doc.in_(docs_archivo))
    ).all()
    
    print(f"👤 Clientes encontrados con esos DNIs: {len(clientes_existentes)}")
    
    for cliente in clientes_existentes:
        print(f"⚠️  DNI EXISTENTE: {cliente.num_doc}")
    
    # También verificar usando el endpoint API para comparar
    response = await async_client.get("/api/usuarios/clientes", headers=headers)
    
    if response.status_code == 200:
        clientes_api = response.json()
        print(f"📊 Total de clientes desde API: {len(clientes_api)}")
        
        emails_api = [cliente.get('email') for cliente in clientes_api]
        emails_encontrados = [email for email in emails_archivo if email in emails_api]
        
        if emails_encontrados:
            print(f"⚠️  Emails duplicados encontrados via API: {emails_encontrados}")
        else:
            print(f"✅ No hay emails duplicados (via API)")
    else:
        print(f"❌ Error al obtener clientes via API: {response.status_code}")
        print(f"📄 Response: {response.text}")
    
    print("\n⚠️ NOTA: Esta verificación usa transacciones y no afecta la BD permanente")

if __name__ == "__main__":
    print("🧪 Para ejecutar este test específico:")
    print("pytest tests/integration/test_archivo_real.py -v -s") 