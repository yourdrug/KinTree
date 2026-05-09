"""
main.py
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging.config

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from genealogy.api.routes import family_routes, person_routes, relation_routes
from identity.api.routes import account_routes, email_routes
from identity.api.routes.auth import (
    bearer_routes as auth_bearer_routes,
)
from identity.api.routes.auth import (
    common_routes as auth_common_routes,
)
from identity.api.routes.auth import (
    cookie_routes as auth_cookie_routes,
)
from identity.api.routes.auth import oauth_routes
from presentation.cli.cli import cli
from presentation.rest.api import internal_routes
from presentation.rest.api.openapi import ApplicationOpenAPIDescription
from presentation.rest.exception_handlers import (
    handle_client_exception,
    handle_http_exception,
    handle_server_exception,
    handle_unexpected_exception,
    handle_validation_exception,
)
from presentation.rest.middlewares.rate_limit import RateLimitMiddleware
from shared.domain.exceptions import ClientException, ServerException
from shared.infrastructure.cache.redis_client import RedisClient
from shared.infrastructure.db.database import database
from shared.infrastructure.db.settings import settings
from shared.infrastructure.logging.configuration import logging_config
from shared.infrastructure.utils import Singleton


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


@Singleton
class Application:
    """
    Application: FastAPI application configurator.
    """

    def __init__(self) -> None:
        """
        __init__: Initializes FastAPI application.
        """

        self.app: FastAPI = FastAPI(
            title=ApplicationOpenAPIDescription.title,
            description=ApplicationOpenAPIDescription.description,
            openapi_tags=ApplicationOpenAPIDescription.tags,
            version="v1",
            docs_url="/_docs",
            redoc_url="/_redoc",
            openapi_url="/openapi.json",
            servers=[
                {"url": "./", "description": "Relative server"},
            ],
            lifespan=lifespan,
        )

        self.set_openapi_version()
        self.configure_logging()
        self.add_middlewares()
        self.add_exception_handlers()
        self.add_routers()
        self.add_mounts()

    def set_openapi_version(self) -> None:
        """
        set_openapi_version: Sets OpenAPI version.
        """

        self.app.openapi_version = "3.0.0"

    def configure_logging(self) -> None:
        """
        configure_logging: Configures application logging.
        """

        logging.config.dictConfig(logging_config)

    def add_middlewares(self) -> None:
        """
        add_middlewares: Adds application middlewares.
        """

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["*"],
            expose_headers=["Set-Cookie"],
        )

        self.app.add_middleware(
            RateLimitMiddleware,
        )

    def add_exception_handlers(self) -> None:
        """
        add_exception_handlers: Registers exception handlers.
        """

        self.app.add_exception_handler(ServerException, handle_server_exception)
        self.app.add_exception_handler(ClientException, handle_client_exception)
        self.app.add_exception_handler(RequestValidationError, handle_validation_exception)
        self.app.add_exception_handler(HTTPException, handle_http_exception)
        self.app.add_exception_handler(Exception, handle_unexpected_exception)

    def add_routers(self) -> None:
        """
        add_routers: Registers API routers.
        """

        self.app.include_router(auth_bearer_routes.router)
        self.app.include_router(auth_cookie_routes.router)
        self.app.include_router(auth_common_routes.router)
        self.app.include_router(oauth_routes.router)

        self.app.include_router(email_routes.router)
        self.app.include_router(account_routes.router)

        self.app.include_router(person_routes.router)
        self.app.include_router(family_routes.router)
        self.app.include_router(relation_routes.router)

        self.app.include_router(internal_routes.router)

    def add_mounts(self) -> None:
        """
        add_mounts: Adds mounts.
        """

        self.app.mount(
            "/static/server",
            StaticFiles(directory="../static/server"),
            name="server",
        )

        self.app.mount(
            "/static/swagger",
            StaticFiles(directory="../static/swagger"),
            name="swagger",
        )

        self.app.mount(
            "/assets",
            StaticFiles(directory="../static/web/assets"),
            name="assets",
        )

        self.app.mount(
            "/",
            StaticFiles(directory="../static/web"),
            name="web",
        )


def create_application() -> FastAPI:
    """
    create_application: Creates FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application.
    """

    application: Application = Application()

    return application.app


if __name__ == "__main__":
    logging.config.dictConfig(logging_config)
    cli.execute_command()
