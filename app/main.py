from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

from app.core.db import init_db
from app.modules.auth.routers import router as auth_router
from app.modules.communities.routers import router as comunidades_router
from app.modules.users.routers import router as usuarios_router

app = FastAPI(
    title="CommuConnect API",
    version="1.0.0",
    description="API de CommuConnect"
)

security = HTTPBearer()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(comunidades_router, prefix="/api/comunidades", tags=["Comunidades"])
app.include_router(usuarios_router,  prefix="/api/usuarios", tags=["Usuarios"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
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
