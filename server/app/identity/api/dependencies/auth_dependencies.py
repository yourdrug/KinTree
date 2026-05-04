"""
identity/api/dependencies/auth_dependencies.py

Зависимости для получения аккаунта из запроса.

Добавлен реэкспорт get_current_token_payload — роуты импортируют
всё из этого модуля, не напрямую из dependencies.py.
"""

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from presentation.rest.dependencies.dependencies import (
    extract_token,
    get_account_service,
    get_current_account_id,
    get_current_token_payload,
)

from identity.application.account.service import AccountService
from identity.domain.entities.account import Account
from identity.infrastructure.auth.jwt_service import decode_access_token


_bearer_optional = HTTPBearer(auto_error=False)


async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    service: AccountService = Depends(get_account_service),
) -> Account:
    """
    Dependency: возвращает аутентифицированный Account из БД.
    Бросает AuthenticationError если токен невалиден или в blacklist.
    """
    return await service.get_account(account_id)


async def get_optional_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    service: AccountService = Depends(get_account_service),
) -> Account | None:
    """
    Dependency: необязательная аутентификация.
    None для гостей, Account для аутентифицированных.
    Blacklist не проверяется для optional — оптимизация для публичных эндпоинтов.
    """
    token = extract_token(request, credentials)
    if not token:
        return None

    payload = decode_access_token(token)
    account_id: str | None = payload.get("sub")
    if not account_id:
        return None

    return await service.get_account(account_id)


# Реэкспорт для удобства импорта в роутах
__all__ = [
    "get_current_account",
    "get_optional_account",
    "get_current_account_id",
    "get_current_token_payload",
]
