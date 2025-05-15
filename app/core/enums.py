from enum import Enum

class TipoUsuario(str, Enum):
    Cliente = "Cliente"
    Administrador = "Administrador"

class TipoDocumento(str, Enum):
    DNI = "DNI"
    CarnetDeExtranjeria = "CARNET DE EXTRANJERIA"

class ModalidadServicio(str, Enum):
    Virtual = "Virtual"
    Presencial = "Presencial"

class TipoSesion(str, Enum):
    Virtual = "Virtual"
    Presencial = "Presencial"

class MetodoPago(str, Enum):
    Tarjeta = "Tarjeta"
    Otro = "Otro"