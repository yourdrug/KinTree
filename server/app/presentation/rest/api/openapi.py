from textwrap import dedent
from typing import ClassVar

from fastapi import status


class ApplicationOpenAPIDescription:
    """
    ApplicationOpenAPIDescription:
    Class containing OpenAPI description for application.
    """

    title: str = "KinTree API"

    description: ClassVar[str] = dedent(
        """
        ## 🌳 KinTree — Платформа для создания генеалогических деревьев.

        ### 📖 Описание сервиса
        KinTree — современный API-сервис для управления семейными связями,
        построения генеалогических деревьев и хранения информации о членах семьи.

        Сервис предоставляет инструменты для:
        - 👤 управления аккаунтами и аутентификацией;
        - 🔐 авторизации через JWT, Cookies и OAuth;
        - 📧 подтверждения email и восстановления доступа;
        - 🧬 создания и редактирования персон;
        - 👨‍👩‍👧‍👦 управления семьями;
        - ❤️ создания родственных и супружеских связей;
        - 🌐 построения графа семейного дерева.

        ### 🚀 Основные возможности
        - JWT Bearer Authentication;
        - Cookie Authentication;
        - OAuth авторизация (Google / Telegram);
        - Управление сессиями;
        - Восстановление пароля;
        - CRUD операции для персон и семей;
        - Построение семейного графа;
        - Rate Limiting и защита API;
        - Redis Cache и асинхронная архитектура.

        ### 🛠️ Технологии
        - FastAPI
        - PostgreSQL
        - Redis
        - AsyncIO
        - OAuth2 / JWT
        - Clean Architecture
        """.strip().replace("        ", "")
    )

    tags: ClassVar[list[dict[str, str]]] = [
        {
            "name": "Auth 🔐",
            "description": "__*Аутентификация, OAuth, JWT, Cookie Sessions*__",
        },
        {
            "name": "Accounts 👤",
            "description": "__*Управление аккаунтами пользователей*__",
        },
        {
            "name": "Persons 🧬",
            "description": "__*Управление персонами в генеалогическом дереве*__",
        },
        {
            "name": "Families 👨‍👩‍👧‍👦",
            "description": "__*Управление семьями и семейными группами*__",
        },
        {
            "name": "Relations ❤️",
            "description": "__*Родственные и супружеские связи*__",
        },
        {
            "name": "Info ℹ️",
            "description": "__*Служебная информация о сервисе*__",
        },
    ]


class InfoOpenAPIDescription:
    """
    InfoOpenAPIDescription: Class, containing openapi description for info module.
    """

    health: ClassVar[str] = "Проверка работоспособности сервера. Возвращает количество секунд со старта сервиса."


class InfoOpenAPIResponses:
    """
    InfoOpenAPIResponses: Class, containing openapi responses for info module.
    """

    health: ClassVar[dict] = {
        status.HTTP_200_OK: {
            "description": "Amount of seconds since service start.",
            "content": {
                "text/plain": {
                    "example": "10",
                },
            },
        }
    }
