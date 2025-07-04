from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, BackgroundTasks, UploadFile, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_cliente_id
from app.modules.communities.services import unir_cliente_a_comunidad
from app.modules.geography.models import Departamento, Distrito
from app.modules.services.schemas import ProfesionalCreate, ProfesionalRead
from app.modules.users.schemas import AdministradorCreate, AdministradorRead, ClienteCreate, ClienteRead, ClienteUpdate, ClienteUpdateIn, ClienteUsuarioFull, UsuarioClienteFull , UsuarioCreate, UsuarioRead,UsuarioBase
from app.modules.users.services import crear_administrador, crear_cliente, crear_usuario, modificar_cliente, obtener_cliente_con_usuario_por_id, procesar_archivo_clientes, reenviar_confirmacion
from app.modules.users.dependencies import get_current_admin
from app.core.logger import logger
from typing import List, Optional
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

@router.post("/usuario", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_session)):
    """
    Registra un nuevo usuario en el sistema.
    - **email**: No debe existir en la base de datos.
    - **nombre**: No debe existir en la base de datos.
    """
    db_user_by_email = db.exec(select(Usuario).where(Usuario.email == usuario.email)).first()
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado."
        )

    db_user_by_name = db.exec(select(Usuario).where(Usuario.nombre == usuario.nombre)).first()
    if db_user_by_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso."
        )
        
    try:
        nuevo_usuario = crear_usuario(db, usuario)
        logger.info(f"Usuario registrado: {usuario.email}")
        return nuevo_usuario
    except Exception as e:
        logger.error(f"Error al registrar usuario {usuario.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario")

@router.post("/cliente", response_model=ClienteRead)
def registrar_cliente(cliente: ClienteCreate, bg: BackgroundTasks, db: Session = Depends(get_session)):
    try:
        nuevo_cliente = crear_cliente(db, cliente, bg)
        logger.info(f"Cliente registrado: {cliente.email}")
        return nuevo_cliente
    except Exception as e:
        logger.error(f"Error al registrar cliente {cliente.email}", exc_info=True)
        print(">>> ERROR DETECTADO <<<")
        print(e)
        raise HTTPException(status_code=500, detail="Error al registrar cliente")

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
@router.get("/clientes", response_model=List[UsuarioClienteFull])
def listar_clientes(session: Session = Depends(get_session)):
    clientes = session.exec(
        select(Usuario).where(
            Usuario.tipo == TipoUsuario.Cliente,
            Usuario.estado == True
        )
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
    

    
@router.put("/cliente/{id_usuario}", response_model=ClienteRead)
def actualizar_cliente(
    id_usuario: int,
    nombre: Optional[str] = Form(None),
    apellido: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    tipo_documento: Optional[str] = Form(None),
    num_doc: Optional[str] = Form(None),
    numero_telefono: Optional[str] = Form(None),
    id_departamento: Optional[int] = Form(None),
    id_distrito: Optional[int] = Form(None),
    direccion: Optional[str] = Form(None),
    fecha_nac: Optional[str] = Form(None),
    genero: Optional[str] = Form(None),
    talla: Optional[float] = Form(None),
    peso: Optional[float] = Form(None),
    db: Session = Depends(get_session),
    current_admin: Usuario = Depends(get_current_admin)
):
    try:
        data = {
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "password": password,
            "tipo_documento": tipo_documento,
            "num_doc": num_doc,
            "numero_telefono": numero_telefono,
            "id_departamento": id_departamento,
            "id_distrito": id_distrito,
            "direccion": direccion,
            "fecha_nac": fecha_nac,
            "genero": genero,
            "talla": talla,
            "peso": peso
        }

        return modificar_cliente(db, id_usuario, data, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {str(e)}")

@router.get("/cliente/id/{id_cliente}", response_model=ClienteUsuarioFull)
def obtener_cliente_por_id_cliente(
    id_cliente: int,
    db: Session = Depends(get_session)
):
    return obtener_cliente_con_usuario_por_id(db, id_cliente)

@router.post("/clientes/carga-masiva")
def carga_masiva_clientes(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_admin: Usuario = Depends(get_current_admin)
):
    try:
        resultado = procesar_archivo_clientes(db, archivo, current_admin.email)
        return {"mensaje": "Carga masiva completada", "resumen": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
from sqlalchemy import func

@router.put("/usuario/cliente/actualizar")
def actualizar_datos_cliente(
    datos: ClienteUpdateIn,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    cliente = session.exec(
        select(Cliente).where(Cliente.id_usuario == current_user.id_usuario)
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    update_data = datos.dict(exclude_unset=True)

    # Si viene el nombre del distrito, buscar el distrito y su departamento
    if "distrito_nombre" in update_data and update_data["distrito_nombre"]:
        nombre_dist = update_data.pop("distrito_nombre")
        distrito = session.exec(
            select(Distrito).where(func.lower(Distrito.nombre) == nombre_dist.strip().lower())
        ).first()
        if not distrito:
            raise HTTPException(status_code=404, detail="Distrito no encontrado")
        update_data["id_distrito"] = distrito.id_distrito
        # Cambia también el departamento según el distrito encontrado
        update_data["id_departamento"] = distrito.id_departamento

    # Si viene el nombre del departamento, buscar el id (solo si no se cambió por el distrito)
    if "departamento_nombre" in update_data and update_data["departamento_nombre"]:
        nombre_dep = update_data.pop("departamento_nombre")
        departamento = session.exec(
            select(Departamento).where(func.lower(Departamento.nombre) == nombre_dep.strip().lower())
        ).first()
        if not departamento:
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
        update_data["id_departamento"] = departamento.id_departamento

    # Actualiza solo los campos enviados
    for field, value in update_data.items():
        setattr(cliente, field, value)
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return {"ok": True, "message": "Datos actualizados correctamente"}