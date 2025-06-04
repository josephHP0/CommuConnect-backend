from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id
from app.modules.communities.services import unir_cliente_a_comunidad
from app.modules.users.schemas import AdministradorCreate, AdministradorRead, ClienteCreate, ClienteRead, ClienteUpdate, UsuarioCreate, UsuarioRead,UsuarioBase
from app.modules.users.services import crear_administrador, crear_cliente, crear_usuario, reenviar_confirmacion
from app.modules.users.dependencies import get_current_admin
from app.core.logger import logger
from typing import List
from app.modules.users.models import Cliente, Usuario
from app.core.enums import TipoUsuario
from app.core.security import hash_password, verify_confirmation_token
from app.modules.communities.schemas import ComunidadContexto
from app.modules.auth.dependencies import get_current_user
from app.modules.users.services import obtener_cliente_desde_usuario, obtener_comunidades_del_cliente, construir_respuesta_contexto
from app.modules.communities.models import Comunidad
from app.modules.communities.services import (
    obtener_comunidad_con_imagen_base64,
    obtener_servicios_con_imagen_base64
)
from app.modules.communities.schemas import ComunidadDetalleOut
from app.modules.billing.schemas import UsoTopesOut
from app.modules.billing.services import (
    obtener_inscripcion_activa,
    es_plan_con_topes,
    obtener_detalle_topes
    )



router = APIRouter()

@router.post("/usuario", response_model=UsuarioRead)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_session)):
    try:
        nuevo_usuario = crear_usuario(db, usuario)
        logger.info(f"Usuario registrado: {usuario.email}")
        return nuevo_usuario
    except Exception as e:
        logger.error(f"Error al registrar usuario {usuario.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario")

@router.post("/cliente", response_model=ClienteRead)
def registrar_cliente(cliente: ClienteCreate,  bg: BackgroundTasks, db: Session = Depends(get_session)):
    try:
        nuevo_cliente = crear_cliente(db, cliente, bg)
        logger.info(f"Cliente registrado: {cliente.email}")
        return nuevo_cliente
    except Exception as e:  # TEMPORAL para ver en consola
        logger.error(f"Error al registrar cliente {cliente.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar cliente")

@router.get("/confirm/{token}", response_model=UsuarioRead)
def confirmar_email(token: str, db: Session = Depends(get_session)):
    """
    Endpoint llamado por el frontend: /confirmar/:token
    Marca el usuario como activo si el token es válido.
    """
    email = verify_confirmation_token(token)
    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enlace inválido o expirado")

    usuario: Usuario | None = db.exec(select(Usuario).where(Usuario.email == email)).first()
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if usuario.estado:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya confirmado")

    usuario.estado = True
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    logger.info(f"Usuario {usuario.email} confirmado")
    return usuario

@router.post("/resend-confirmation")
def resend_confirmation(email: str,bg: BackgroundTasks,db: Session = Depends(get_session)):
    return reenviar_confirmacion(db, email, bg)


@router.post("/administrador", response_model=AdministradorRead)
def registrar_administrador(administrador: AdministradorCreate, db: Session = Depends(get_session)):
    try:
        nuevo_admin = crear_administrador(db, administrador)
        logger.info(f"Administrador registrado: {administrador.email}")
        return nuevo_admin
    except Exception as e:
        logger.error(f"Error al registrar administrador {administrador.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar administrador")

#Endpoint para listar todos los clientes
@router.get(
    "/clientes",
    response_model=List[UsuarioBase],
    summary="Listado de clientes"
)
def listar_clientes(
    session: Session = Depends(get_session)
):
    """
    Devuelve todos los usuarios cuyo tipo sea 'Cliente'.
    """
    clientes = session.exec(
        select(Usuario).where(Usuario.tipo == TipoUsuario.Cliente, Usuario.estado == True)  # Solo clientes activos
    ).all()
    return clientes

#Endpoint para regisrar a un cliente a una comunidad
@router.post("/unir_cliente_comunidad")
def unir_cliente_comunidad(
    id_comunidad: int,
    session: Session = Depends(get_session),
    id_cliente: int = Depends(get_current_cliente_id)
):
    return unir_cliente_a_comunidad(session, id_cliente, id_comunidad)



@router.get("/usuario/comunidades", response_model=List[ComunidadContexto])
def listar_comunidades_usuario(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    print(f"\n[INICIO] Usuario autenticado: {current_user.email} (ID: {current_user.id_usuario})")

    try:
        # Paso 1: obtener cliente vinculado al usuario
        try:
            print(" Buscando cliente vinculado al usuario...")
            cliente = obtener_cliente_desde_usuario(session, current_user)
            print(f" Cliente encontrado: ID {cliente.id_cliente}")
        except HTTPException as e:
            print(f" Error HTTP al buscar cliente: {e.detail}")
            raise e
        except Exception as e:
            print(f" Error inesperado al buscar cliente: {e}")
            raise HTTPException(
                status_code=404,
                detail=f"[cliente] No se encontró cliente vinculado al usuario {current_user.id_usuario}: {str(e)}"
            )

        # Paso 2: obtener comunidades del cliente
        try:
            print("Buscando comunidades del cliente...")
            comunidades = obtener_comunidades_del_cliente(session, cliente.id_cliente) # type: ignore
            print(f" Comunidades encontradas: {[c.nombre for c in comunidades]}")
        except HTTPException as e:
            print(f" Error HTTP al obtener comunidades: {e.detail}")
            raise e
        except Exception as e:
            print(f" Error inesperado al obtener comunidades: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"[comunidades] Error al obtener comunidades del cliente {cliente.id_cliente}: {str(e)}"
            )

        # Paso 3: construir respuesta final con servicios
        try:
            print("Construyendo respuesta final con servicios...")
            respuesta = construir_respuesta_contexto(session, comunidades,cliente.id_cliente) # type: ignore
            print(" Respuesta construida correctamente.")
        except HTTPException as e:
            print(f" Error HTTP al construir respuesta: {e.detail}")
            raise e
        except Exception as e:
            print(f" Error inesperado al construir respuesta: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"[respuesta] Error desconocido al construir la respuesta: {str(e)}"
            )

        return respuesta

    except HTTPException as e:
        print(f" HTTPException final capturada: {e.detail}")
        raise e
    except Exception as e:
        print(f" Excepción general capturada: {e}")
        raise HTTPException(status_code=500, detail=f"[general] Error inesperado: {str(e)}")



@router.get("/usuario/comunidad/{id_comunidad}")
def obtener_comunidad_detalle(
    id_comunidad: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    comunidad, imagen_base64 = obtener_comunidad_con_imagen_base64(session, id_comunidad)
    servicios_out = obtener_servicios_con_imagen_base64(session, id_comunidad)

    return ComunidadDetalleOut(
        id_comunidad=comunidad.id_comunidad, # type: ignore
        nombre=comunidad.nombre,
        slogan=comunidad.slogan,  # Usado como texto descriptivo
        imagen=imagen_base64,
        servicios=servicios_out
    )


@router.get("/usuario/comunidad/{id_comunidad}/topes", response_model=UsoTopesOut)
def obtener_uso_topes(
    id_comunidad: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    cliente = obtener_cliente_desde_usuario(session, current_user)
    id_cliente = cliente.id_cliente

    inscripcion = obtener_inscripcion_activa(session, id_cliente, id_comunidad) # type: ignore

    if not es_plan_con_topes(session, inscripcion.id_inscripcion): # type: ignore
        return UsoTopesOut(estado="Ilimitado")

    detalle = obtener_detalle_topes(session, inscripcion.id_inscripcion) # type: ignore
    topes_disponibles = detalle["topes_disponibles"]
    topes_consumidos = detalle["topes_consumidos"]
    total = topes_disponibles + topes_consumidos

    return UsoTopesOut(
        plan="Plan por Topes",
        topes_disponibles=topes_disponibles,
        topes_consumidos=topes_consumidos,
        estado=f"Restan {topes_disponibles} de {total}"
    )



#Endpoint para eliminar cliente logicamente (solo administradores)
@router.delete("/eliminar_cliente/{id_cliente}")
def eliminar_cliente(
    id_cliente: int,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin)
):
    """
    Elimina un cliente de forma lógica (cambia su estado a inactivo).
    Solo accesible para administradores.
    """
    try:
        cliente = session.exec(
            select(Cliente).where(Cliente.id_cliente == id_cliente)
        ).first()
        
        if not cliente or not cliente.usuario:
            raise HTTPException(status_code=404, detail="Cliente o usuario no encontrado")

        cliente.usuario.estado = False
        cliente.usuario.fecha_modificacion = datetime.utcnow()
        cliente.usuario.modificado_por = current_admin.email

        session.add(cliente.usuario)
        session.commit()
        session.refresh(cliente.usuario)

        logger.info(f"Cliente {cliente.usuario.email} eliminado lógicamente por {current_admin.email}")
        return {"message": "Cliente eliminado lógicamente"}
    
    except HTTPException as e:
        raise e
    

    
#Endpoint para modificar cliente
@router.put("/modificar_cliente/{id_cliente}", response_model=ClienteRead)
def modificar_cliente(
    id_cliente: int,
    cliente_data: ClienteUpdate,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_admin)
):
    """
    Modifica los datos de un cliente.
    Solo accesible para administradores.
    """
    try:
        cliente = session.exec(
            select(Cliente).where(Cliente.id_cliente == id_cliente)
        ).first()
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Actualiza campos de Cliente
        data = cliente_data.dict(exclude_unset=True)
        password = data.pop("password", None)

        usuario_fields = {"nombre", "apellido", "email"}
        for key, value in data.items():
            if key in usuario_fields:
                setattr(cliente.usuario, key, value)
            else:
                setattr(cliente, key, value)

        # Actualiza contraseña si corresponde
        if password:
            cliente.usuario.password = hash_password(password) # type: ignore

        # Auditoría
        cliente.usuario.fecha_modificacion = datetime.utcnow() # type: ignore
        cliente.usuario.modificado_por = current_admin.email # type: ignore

        session.add(cliente)
        session.commit()
        session.refresh(cliente)

        logger.info(f"Cliente {cliente.usuario.email} modificado por {current_admin.email}") # type: ignore
        return ClienteRead.from_orm(cliente)

    except HTTPException as e:
        raise e