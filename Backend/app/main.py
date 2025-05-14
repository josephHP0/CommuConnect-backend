from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.db import init_db
from app.routers import auth, comunidades, administradores
from app.models.usuario import Usuario
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi.openapi.models import APIKey, APIKeyIn, SecuritySchemeType
from fastapi.openapi.utils import get_openapi

app = FastAPI()
security = HTTPBearer()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(comunidades.router, prefix="/api/comunidades", tags=["Comunidades"])
app.include_router(administradores.router, prefix="/api/administradores", tags=["Administradores"])