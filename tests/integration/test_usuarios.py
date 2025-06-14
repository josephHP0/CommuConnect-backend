import sys
import os
import pytest
from fastapi import HTTPException
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.modules.users.routers import registrar_usuario
from app.modules.users.schemas import UsuarioCreate
from app.core.db import get_session, Session

# Usar una sesión de base de datos directa para controlar las transacciones
# y asegurar que los datos persistan dentro de una misma prueba.

def test_registro_usuario_exitoso(session_test: Session):
    payload = UsuarioCreate(
        nombre="ExitosoUnico",
        apellido="Test",
        email="exitosounico@test.com",
        tipo="CLIENTE",
        password="Segura123"
    )
    nuevo_usuario = registrar_usuario(usuario=payload, db=session_test)
    assert nuevo_usuario.email == "exitosounico@test.com"

def test_registro_usuario_email_duplicado(session_test: Session):
    # Primero, creamos un usuario
    payload1 = UsuarioCreate(
        nombre="OriginalEmail",
        apellido="Duplicado",
        email="emailduplicado@test.com",
        tipo="CLIENTE",
        password="Clave123"
    )
    registrar_usuario(usuario=payload1, db=session_test)

    # Ahora, intentamos crear otro con el mismo email
    payload2 = UsuarioCreate(
        nombre="OtroUsuarioEmail",
        apellido="Conflictivo",
        email="emailduplicado@test.com", # Email repetido
        tipo="CLIENTE",
        password="Clave456"
    )
    with pytest.raises(HTTPException) as excinfo:
        registrar_usuario(usuario=payload2, db=session_test)
    
    assert excinfo.value.status_code == 409
    assert "El email ya está registrado" in excinfo.value.detail

def test_registro_usuario_nombre_duplicado(session_test: Session):
    # Primero, creamos un usuario
    payload1 = UsuarioCreate(
        nombre="NombreEnUsoUnico",
        apellido="Original",
        email="nombreoriginalunico@test.com",
        tipo="CLIENTE",
        password="ClaveOriginal"
    )
    registrar_usuario(usuario=payload1, db=session_test)

    # Ahora, intentamos crear otro con el mismo nombre
    payload2 = UsuarioCreate(
        nombre="NombreEnUsoUnico", # Nombre repetido
        apellido="Conflictivo",
        email="nombreconflictivounico@test.com",
        tipo="CLIENTE",
        password="ClaveConflictiva"
    )
    with pytest.raises(HTTPException) as excinfo:
        registrar_usuario(usuario=payload2, db=session_test)

    assert excinfo.value.status_code == 409
    assert "El nombre de usuario ya está en uso" in excinfo.value.detail
