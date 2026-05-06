"""
main.py
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging.config
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from genealogy.api.routes import family_routes, person_routes, relation_routes
from identity.api.routes import account_routes
from identity.api.routes.auth import (
    bearer_routes as auth_bearer_routes,
)
from identity.api.routes.auth import (
    common_routes as auth_common_routes,
)
from identity.api.routes.auth import (
    cookie_routes as auth_cookie_routes,
)
from presentation.cli.cli import cli
from presentation.rest.exception_handlers import register_exception_handlers
from presentation.rest.middlewares.rate_limit import RateLimitMiddleware
from shared.infrastructure.cache.redis_client import RedisClient
from shared.infrastructure.db.database import database
from shared.infrastructure.db.settings import settings
from shared.infrastructure.logging.configuration import logging_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan для FastAPI: выполняется при старте и завершении приложения.
    """

    await database.connect()
    await RedisClient.init()

    yield  # приложение работает

    await RedisClient.close()
    await database.disconnect()


def create_app() -> FastAPI:
    """Создаёт и возвращает сконфигурированное FastAPI-приложение."""

    app = FastAPI(
        title="KinTree API",
        description="API для работы с KinTree",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.server_start_time = time.time()

    logging.config.dictConfig(logging_config)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Set-Cookie"],
    )
    app.add_middleware(RateLimitMiddleware)

    app.include_router(auth_common_routes.router)
    app.include_router(auth_bearer_routes.router)
    app.include_router(auth_cookie_routes.router)
    app.include_router(account_routes.router)
    app.include_router(person_routes.router)
    app.include_router(family_routes.router)
    app.include_router(relation_routes.router)

    register_exception_handlers(app)

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
    logging.config.dictConfig(logging_config)
    cli.execute_command()
