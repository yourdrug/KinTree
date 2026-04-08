from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import time

from api.accounts import routes as users_routes
from api.persons import routes as person_routes
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.common.database import database
from infrastructure.common.handlers import handle_fastapi_validation_exceptions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan для FastAPI: выполняется при старте и завершении приложения.
    """

    await database.connect()

    yield  # Точка, где приложение работает

    await database.disconnect()


def create_app() -> FastAPI:
    """
    Создает и возвращает FastAPI приложение с конфигурацией, роутерами и middleware.
    """

    app = FastAPI(
        title="KinTree API",
        description="API для работы с KinTree",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.server_start_time = time.time()

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(users_routes.router)
    app.include_router(person_routes.router)

    app.add_exception_handler(RequestValidationError, handle_fastapi_validation_exceptions)

    # Основные endpoints
    @app.get("/")
    async def root() -> dict:
        return {"message": "service KinTree", "docs": "/docs", "redoc": "/redoc"}

    @app.get("/health")
    async def health_check() -> int:
        return round((time.time() - app.state.server_start_time) * 100)

    return app


# Экземпляр приложения для uvicorn/gunicorn
app = create_app()
