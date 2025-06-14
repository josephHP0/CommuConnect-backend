import pytz
from datetime import datetime

def convert_utc_to_local(utc_dt: datetime, target_tz_name: str = "America/Lima") -> datetime:
    """
    Convierte un objeto datetime de UTC a una zona horaria específica.
    Si el datetime es "naive" (sin zona horaria), asume que es UTC.
    """
    if not utc_dt:
        return None
    
    utc_tz = pytz.utc
    
    # Si el datetime no tiene zona horaria, se la asignamos como UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_tz.localize(utc_dt)
    
    # Convertimos a la zona horaria de destino
    target_tz = pytz.timezone(target_tz_name)
    return utc_dt.astimezone(target_tz)

def convert_local_to_utc(local_dt: datetime, local_tz_name: str = "America/Lima") -> datetime:
    """
    Convierte un datetime "naive" (que se asume está en una zona horaria local) a UTC.
    """
    if not local_dt:
        return None
        
    local_tz = pytz.timezone(local_tz_name)
    
    # Asigna la zona horaria local al datetime "naive"
    aware_local_dt = local_tz.localize(local_dt)
    
    # Convierte a UTC
    return aware_local_dt.astimezone(pytz.utc) 