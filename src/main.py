from fastapi import FastAPI

from src.api.middlewares.error_handling import register_exception_handlers
from src.api.routes.auth import router as auth_router
from src.api.routes.conversations import router as conversations_router
from src.api.routes.documents import router as documents_router
from src.api.routes.health import router as health_router

API_V1_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(title="ContextFlow AI", version="0.1.0")

    register_exception_handlers(app)

    app.include_router(health_router, prefix=API_V1_PREFIX)
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(documents_router, prefix=API_V1_PREFIX)
    app.include_router(conversations_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
