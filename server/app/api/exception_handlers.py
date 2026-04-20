"""
api/exception_handlers.py

Единый обработчик исключений для FastAPI.

Принципы:
- Один маппинг exception_type → status_code, не разбросан по нескольким функциям.
- Все доменные исключения имеют единый интерфейс as_dict() — нет дублирования.
- handle_domain_exception() — центральный обработчик клиентских ошибок.
- Неожиданные ошибки логируются с exc_info и возвращают 500.
"""

from __future__ import annotations

from logging import Logger, getLogger

from domain.exceptions import (
    AccountBlockedError,
    AuthenticationError,
    ClientException,
    ConflictError,
    DatabaseError,
    DomainValidationError,
    FamilyDomainError,
    FilterValidationError,
    NotFoundError,
    PermissionDeniedError,
    PersonDomainError,
    RelationDomainError,
    ServerException,
)
from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse


logger: Logger = getLogger("default")


# ── Маппинг исключений → HTTP-коды ───────────────────────────────────────────

_CLIENT_STATUS_MAP: dict[type[ClientException], int] = {
    DomainValidationError: status.HTTP_400_BAD_REQUEST,
    PersonDomainError: status.HTTP_400_BAD_REQUEST,
    FamilyDomainError: status.HTTP_400_BAD_REQUEST,
    RelationDomainError: status.HTTP_400_BAD_REQUEST,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    AccountBlockedError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    FilterValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ClientException: status.HTTP_400_BAD_REQUEST,  # fallback
}

_SERVER_STATUS_MAP: dict[type[ServerException], int] = {
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ServerException: status.HTTP_500_INTERNAL_SERVER_ERROR,  # fallback
}


def _json(data: dict, status_code: int) -> JSONResponse:
    return JSONResponse(content=data, status_code=status_code)


def _error(message: str, errors: dict | None = None) -> dict:
    result: dict = {"message": message}
    if errors:
        result["errors"] = errors
    return result


# ── Handlers ──────────────────────────────────────────────────────────────────


async def handle_client_exception(request: Request, exc: Exception) -> JSONResponse:
    """4xx — клиентские ошибки (доменные инварианты, авторизация, not found)."""
    if not isinstance(exc, ClientException):
        logger.error("Unexpected exception in client handler", exc_info=exc)
        return _json(_error("Internal Server Error"), status.HTTP_500_INTERNAL_SERVER_ERROR)

    status_code = status.HTTP_400_BAD_REQUEST
    for exc_type, code in _CLIENT_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            status_code = code
            break

    return _json(exc.as_dict(), status_code)


async def handle_server_exception(request: Request, exc: Exception) -> JSONResponse:
    """5xx — серверные ошибки."""
    if not isinstance(exc, ServerException):
        logger.critical("Unexpected exception in server handler", exc_info=exc)
        return _json(_error("Internal Server Error"), status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.error("Server exception: %s", exc, exc_info=True)

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    for exc_type, code in _SERVER_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            status_code = code
            break

    return _json(exc.as_dict(), status_code)


async def handle_validation_exception(request: Request, exc: Exception) -> JSONResponse:
    """422 — ошибки валидации Pydantic (RequestValidationError)."""
    if not isinstance(exc, RequestValidationError):
        logger.critical("Unexpected exception in validation handler", exc_info=exc)
        return _json(_error("Internal Server Error"), status.HTTP_500_INTERNAL_SERVER_ERROR)

    _MESSAGES = {
        "missing": "Обязательное поле",
        "extra_forbidden": "Запрещено добавлять лишние поля",
        "frozen_field": "Нельзя изменять это поле",
        "int_parsing": "Должно быть целым числом",
        "float_parsing": "Должно быть числом (дробь разрешена)",
        "bool_parsing": "Должно быть True или False",
        "string_type": "Должно быть строкой",
        "greater_than": "Должно быть больше {gt}",
        "less_than": "Должно быть меньше {lt}",
        "multiple_of": "Должно быть кратно {multiple_of}",
        "string_too_short": "Минимум {min_length} символов",
        "string_too_long": "Максимум {max_length} символов",
        "string_pattern_mismatch": "Некорректный формат (формат {pattern})",
        "enum": "Допустимые значения: {expected}",
        "literal_error": "Допустимо только: {expected}",
        "date_parsing": "Некорректная дата (формат: ГГГГ-ММ-ДД)",
        "time_parsing": "Некорректное время (формат: ЧЧ:ММ:СС)",
        "datetime_parsing": "Некорректная дата и время (формат: ГГГГ-ММ-ДДTЧЧ:ММ:СС)",
        "datetime_from_date_parsing": "Некорректная дата и время (формат: ГГГГ-ММ-ДДTЧЧ:ММ:СС)",
        "value_error": "Некорректное значение: {error}",
    }

    errors: dict = {}
    for error in exc.errors():
        if "loc" not in error or not error["loc"]:
            continue
        field = str(error["loc"][-1])
        tmpl = _MESSAGES.get(error.get("type", ""), error.get("msg", "Ошибка"))
        errors[field] = tmpl.format(**error.get("ctx", {}))

    content = _error("Ошибка валидации", errors) if errors else _error("Ошибка валидации")
    return _json(content, status.HTTP_422_UNPROCESSABLE_ENTITY)


async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    """Обрабатывает стандартные FastAPI HTTPException."""
    if not isinstance(exc, HTTPException):
        logger.critical("Unexpected exception in http handler", exc_info=exc)
        return _json(_error("Internal Server Error"), status.HTTP_500_INTERNAL_SERVER_ERROR)

    _AUTH_MESSAGES = {
        "Not authenticated": "Не авторизован",
        "Invalid authentication credentials": "Неверные учетные данные",
    }

    if isinstance(exc.detail, dict):
        content = _error(str(exc.detail))
    else:
        content = _error(_AUTH_MESSAGES.get(exc.detail, exc.detail))

    return _json(content, exc.status_code)


async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Fallback для необработанных исключений."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return _json(_error("Internal Server Error"), status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Регистрирует все обработчики в FastAPI-приложении.
    Вызывается в create_app().
    """
    app.add_exception_handler(ServerException, handle_server_exception)
    app.add_exception_handler(ClientException, handle_client_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
