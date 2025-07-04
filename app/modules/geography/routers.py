from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_session
from app.modules.geography.models import Departamento, Distrito


router = APIRouter()

@router.get("/departamentos", response_model=List[dict])
def listar_departamentos(session: Session = Depends(get_session)):
    departamentos = session.query(Departamento).all()
    return [{"id_departamento": d.id_departamento, "nombre": d.nombre} for d in departamentos]

@router.get("/distritos/{id_departamento}", response_model=List[dict])
def listar_distritos_por_departamento(id_departamento: int, session: Session = Depends(get_session)):
    distritos = session.query(Distrito).filter(Distrito.id_departamento == id_departamento).all() # type: ignore
    return [{"id_distrito": d.id_distrito, "nombre": d.nombre} for d in distritos]