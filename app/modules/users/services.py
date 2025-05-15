from sqlmodel import Session, select
from app.modules.users.models import Usuario, Cliente
from app.modules.users.schemas import UserCreate
from app.core.security import hash_password
from fastapi import HTTPException, status
from datetime import datetime


def crear_cliente(db: Session, datos: UserCreate, creado_por: str = "sistema"):
    # Validación: Contraseñas coinciden
    if datos.password != datos.repetir_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden.")

    # Validación: Email único
    if db.exec(select(Usuario).where(Usuario.email == datos.email)).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado.")

    # Validación: Documento único
    if db.exec(select(Cliente).where(Cliente.num_doc == datos.num_doc)).first():
        raise HTTPException(status_code=400, detail="El número de documento ya existe.")

    # Crear usuario
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        apellido=datos.apellido,
        email=datos.email,
        password=hash_password(datos.password),
        tipo="Cliente",
        creado_por=creado_por,
        fecha_creacion=datetime.utcnow(),
        estado=True
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Crear cliente asociado
    nuevo_cliente = Cliente(
        id_usuario=nuevo_usuario.id_usuario,
        tipo_documento=datos.tipo_documento,
        num_doc=datos.num_doc,
        numero_telefono=datos.numero_telefono,
        id_departamento=datos.id_departamento,
        id_distrito=datos.id_distrito,
        direccion=datos.direccion,
        fecha_nac=datos.fecha_nac,
        genero=datos.genero,
        talla=datos.talla,
        peso=datos.peso
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)

    return {
        "mensaje": "Cliente registrado correctamente",
        "id_usuario": nuevo_usuario.id_usuario,
        "id_cliente": nuevo_cliente.id_cliente
    }

