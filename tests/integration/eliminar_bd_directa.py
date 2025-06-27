import sys
import os
import pytest
from sqlmodel import Session, select, delete
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.db import get_session
from app.modules.users.models import Cliente, Usuario

@pytest.mark.asyncio 
async def test_eliminar_datos_bd_directa():
    """
    Elimina directamente desde la BD los datos de Karolyn Torre y Pepito Escam
    """
    print(f"\n🗑️ Eliminando datos directamente desde la BD...")
    
    # Emails específicos a eliminar
    emails_a_eliminar = ["karol@demo.com", "pep@demo.com"]
    docs_a_eliminar = ["72357812", "85768645"]
    
    # Usar el generador de sesión de la aplicación
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        print(f"📊 Buscando usuarios con emails: {emails_a_eliminar}")
        
        # Buscar usuarios por email
        usuarios_a_eliminar = session.exec(
            select(Usuario).where(Usuario.email.in_(emails_a_eliminar))
        ).all()
        
        print(f"🎯 Usuarios encontrados: {len(usuarios_a_eliminar)}")
        
        for usuario in usuarios_a_eliminar:
            print(f"\n🔍 Procesando: {usuario.nombre} {usuario.apellido} - {usuario.email}")
            
            # Buscar cliente asociado
            cliente = session.exec(
                select(Cliente).where(Cliente.id_usuario == usuario.id_usuario)
            ).first()
            
            if cliente:
                print(f"👤 Cliente encontrado con ID: {cliente.id_cliente}, DNI: {cliente.num_doc}")
                
                # Eliminar cliente primero (por foreign key)
                session.delete(cliente)
                print(f"✅ Cliente eliminado de la tabla 'cliente'")
            else:
                print(f"⚠️ No se encontró cliente asociado al usuario")
            
            # Eliminar usuario
            session.delete(usuario)
            print(f"✅ Usuario eliminado de la tabla 'usuario'")
        
        # Confirmar cambios
        session.commit()
        print(f"\n💾 Cambios confirmados en la base de datos")
        
        # Verificar eliminación
        print(f"\n🔍 Verificando eliminación...")
        usuarios_restantes = session.exec(
            select(Usuario).where(Usuario.email.in_(emails_a_eliminar))
        ).all()
        
        if len(usuarios_restantes) == 0:
            print(f"✅ ¡Perfecto! Todos los usuarios fueron eliminados correctamente")
        else:
            print(f"⚠️ Aún quedan {len(usuarios_restantes)} usuarios:")
            for u in usuarios_restantes:
                print(f"   - {u.email}")
        
        # Verificar clientes por DNI
        clientes_restantes = session.exec(
            select(Cliente).where(Cliente.num_doc.in_(docs_a_eliminar))
        ).all()
        
        if len(clientes_restantes) == 0:
            print(f"✅ ¡Perfecto! Todos los clientes fueron eliminados correctamente")
        else:
            print(f"⚠️ Aún quedan {len(clientes_restantes)} clientes:")
            for c in clientes_restantes:
                print(f"   - DNI: {c.num_doc}")
                
    except Exception as e:
        print(f"❌ Error durante la eliminación: {str(e)}")
        session.rollback()
        raise e
    finally:
        session.close()
        print(f"\n🔒 Sesión de BD cerrada")

if __name__ == "__main__":
    print("🧪 Para ejecutar este script de eliminación directa:")
    print("pytest tests/integration/eliminar_bd_directa.py -v -s") 