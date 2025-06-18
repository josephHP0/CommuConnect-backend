from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from app.core.db import init_db
from app.modules.auth.routers import router as auth_router
from app.modules.communities.routers import router as comunidades_router
from app.modules.users.routers import router as usuarios_router
from app.modules.billing.routers import router as billing_router
from app.modules.services.routers import router as  services_router
from app.modules.reservations.routers import router as  reservations_router
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.DEBUG)


app = FastAPI(debug=True)

origins = [
    #"http://commuconnect-frontend-v1.s3-website-us-east-1.amazonaws.com"
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # O usa ["*"] temporalmente para probar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBearer()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(comunidades_router, prefix="/api/comunidades", tags=["Comunidades"])
app.include_router(usuarios_router,  prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])
app.include_router(services_router, prefix="/api/services", tags=["Services"])
app.include_router(reservations_router, prefix="/api/reservations", tags=["Reservations"])

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
