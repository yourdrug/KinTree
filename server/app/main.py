from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import time

from api.exception_handlers import (
    handle_fastapi_expected_client_exceptions,
    handle_fastapi_expected_server_exceptions,
    handle_fastapi_http_exceptions,
    handle_fastapi_unexpected_exceptions,
    handle_fastapi_validation_exceptions,
)
from api.routes import account_routes, family_routes, person_routes
from domain.exceptions import ClientException, ServerException
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.db.database import database


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

    app.include_router(account_routes.router)
    app.include_router(person_routes.router)
    app.include_router(family_routes.router)

    app.add_exception_handler(ServerException, handle_fastapi_expected_server_exceptions)
    app.add_exception_handler(ClientException, handle_fastapi_expected_client_exceptions)
    app.add_exception_handler(RequestValidationError, handle_fastapi_validation_exceptions)
    app.add_exception_handler(HTTPException, handle_fastapi_http_exceptions)
    app.add_exception_handler(Exception, handle_fastapi_unexpected_exceptions)

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
