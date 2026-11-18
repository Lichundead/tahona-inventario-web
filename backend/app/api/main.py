from fastapi import APIRouter

from app.api.routes import (
    alertas,
    categorias,
    login,
    private,
    productos,
    transacciones,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(categorias.router)
api_router.include_router(productos.router)
api_router.include_router(transacciones.router)
api_router.include_router(alertas.router)


if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
