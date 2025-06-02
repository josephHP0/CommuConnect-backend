from sqlalchemy.orm import Session
from app.modules.reservations.models import Sesion, SesionVirtual, Profesional  # ajusta el import según tu estructura
from sqlmodel import select

def obtener_profesionales_por_servicio(session: Session, id_servicio: int):
    sesiones = session.exec(
        select(Sesion.id_sesion).where(Sesion.id_servicio == id_servicio)
    ).all()
    
    print(f"Sesiones encontradas para id_servicio={id_servicio}: {sesiones}")
    
    if not sesiones:
        return []

    sesiones_virtuales = session.exec(
        select(SesionVirtual).where(SesionVirtual.id_sesion.in_(sesiones))
    ).all()

    print(f"Sesiones virtuales encontradas: {len(sesiones_virtuales)} registros")

    profesionales_ids = list(set(sv.id_profesional for sv in sesiones_virtuales))
    
    if not profesionales_ids:
        return []

    profesionales = session.exec(
        select(Profesional).where(Profesional.id_profesional.in_(profesionales_ids))
    ).all()

    return profesionales




