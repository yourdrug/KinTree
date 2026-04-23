from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from genealogy.api.routes import family_routes, person_routes, relation_routes
from identity.api.routes import account_routes, auth_routes
from presentation.cli.cli import cli
from presentation.rest.exception_handlers import register_exception_handlers
from shared.infrastructure.db.database import database
from shared.infrastructure.db.settings import settings


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
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_routes.router)
    app.include_router(account_routes.router)
    app.include_router(person_routes.router)
    app.include_router(family_routes.router)
    app.include_router(relation_routes.router)

    register_exception_handlers(app)

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

if __name__ == "__main__":
    cli.execute_command()
