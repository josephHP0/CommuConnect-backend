from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.core.db import init_db
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

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="CommuConnect API",
        version="1.0.0",
        description="API de CommuConnect",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi