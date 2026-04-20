"""
domain/exceptions.py

Иерархия доменных исключений.

Принципы:
- ClientException  → проблема на стороне клиента (4xx)
- ServerException  → проблема на стороне сервера (5xx)
- DomainError      → нарушение бизнес-инварианта (400)
- NotFoundError    → объект не найден (404)
- ConflictError    → конфликт состояния (409)
- AuthError        → проблема аутентификации/авторизации (401/403)
- FilterError      → некорректный фильтр (422)

Все исключения имеют единый интерфейс: message + errors + dict().
"""

from __future__ import annotations

from typing import Any


# ── Base ─────────────────────────────────────────────────────────────────────


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, errors: dict[str, Any] | None = None) -> None:
        self.message = message
        self.errors = errors
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, errors={self.errors!r})"

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"message": self.message}
        if self.errors:
            result["errors"] = self.errors
        return result


# ── Server ────────────────────────────────────────────────────────────────────


class ServerException(AppException):
    """Ошибка на стороне сервера (5xx)."""


class DatabaseError(ServerException):
    """Ошибка взаимодействия с базой данных."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            message="Ошибка взаимодействия с БД",
            errors={"detail": detail} if detail else None,
        )


# ── Client ────────────────────────────────────────────────────────────────────


class ClientException(AppException):
    """Ошибка на стороне клиента (4xx)."""


class DomainValidationError(ClientException):
    """
    Нарушение бизнес-инварианта (400).

    Удобный конструктор: принимает field + message ИЛИ словарь errors.
    """

    def __init__(
        self,
        message: str = "Ошибка валидации",
        errors: dict[str, Any] | None = None,
        *,
        field: str | None = None,
    ) -> None:
        if field is not None and errors is None:
            errors = {field: message}
            message = "Ошибка валидации"
        super().__init__(message=message, errors=errors)


class PersonDomainError(DomainValidationError):
    """Нарушение инварианта агрегата Person."""


class FamilyDomainError(DomainValidationError):
    """Нарушение инварианта агрегата Family."""


class RelationDomainError(DomainValidationError):
    """Нарушение инварианта связей между персонами."""


class NotFoundError(ClientException):
    """Запрошенный ресурс не найден (404)."""

    def __init__(self, resource: str, resource_id: str | None = None) -> None:
        msg = f"{resource} не найден"
        errors = {resource.lower(): msg}
        if resource_id:
            errors["id"] = resource_id
        super().__init__(message=msg, errors=errors)


class ConflictError(ClientException):
    """Конфликт состояния — ресурс уже существует (409)."""


class AuthenticationError(ClientException):
    """Ошибка аутентификации — невалидный/истёкший токен (401)."""


class PermissionDeniedError(ClientException):
    """Недостаточно прав (403)."""

    def __init__(self, required: str | list[str] | None = None) -> None:
        errors: dict[str, Any] = {}
        if isinstance(required, str):
            errors["required_permission"] = required
        elif isinstance(required, list):
            errors["required_any_of"] = required
        super().__init__(message="Недостаточно прав", errors=errors or None)


class AccountBlockedError(ClientException):
    """Аккаунт заблокирован (403)."""

    def __init__(self) -> None:
        super().__init__(
            message="Аккаунт заблокирован",
            errors={"account": "Ваш аккаунт заблокирован. Обратитесь в поддержку."},
        )


class FilterValidationError(ClientException):
    """Некорректные параметры фильтрации (422)."""
