from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



API_PREFIX = "/file-converter"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan для FastAPI: выполняется при старте и завершении приложения.
    """

    yield  # Точка, где приложение работает



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

    # Основные endpoints
    @app.get("/")
    async def root() -> dict:
        return {"message": "service KinTree", "docs": "/docs", "redoc": "/redoc"}

    @app.get(f"/health")
    async def health_check() -> int:
        return round((time.time() - app.state.server_start_time) * 100)

    return app


# Экземпляр приложения для uvicorn/gunicorn
app = create_app()
