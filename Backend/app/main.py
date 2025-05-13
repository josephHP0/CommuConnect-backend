from fastapi import FastAPI
from app.db import init_db
from app.routers import auth, comunidades, administradores
from app.models.usuario import Usuario

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(comunidades.router, prefix="/api/comunidades", tags=["Comunidades"])
app.include_router(administradores.router, prefix="/api/administradores", tags=["Administradores"])