"""
identity/api/dependencies/auth_dependencies.py

Зависимости для получения аккаунта из запроса.

_bearer_optional объявлен один раз в presentation/rest/dependencies/dependencies.py
и реэкспортируется здесь для удобства. Дублирование устранено.
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from presentation.rest.dependencies.dependencies import (
    bearer,
    extract_token,
    get_account_service,
    get_current_account_id,
    get_current_token_payload,
    get_token_service_dep,
)

from identity.application.account.service import AccountService
from identity.domain.entities.account import Account
from identity.domain.ports.token_service import ITokenService


async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    service: AccountService = Depends(get_account_service),
) -> Account:
    """
    Dependency: возвращает аутентифицированный Account из БД.
    Бросает AuthenticationError если токен невалиден или в blacklist.
    Бросает NotFoundError если аккаунт не найден (аномалия).
    """
    return await service.get_account(account_id)


async def get_optional_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    service: AccountService = Depends(get_account_service),
    token_service: ITokenService = Depends(get_token_service_dep),
) -> Account | None:
    """
    Dependency: необязательная аутентификация.
    None для гостей, Account для аутентифицированных.
    Blacklist не проверяется — оптимизация для публичных эндпоинтов.
    """
    token = extract_token(request, credentials)
    if not token:
        return None

    payload = token_service.decode_access_token(token)
    account_id: str = payload.account_id

    return await service.get_account(account_id)


__all__ = [
    "get_current_account",
    "get_optional_account",
    "get_current_account_id",
    "get_current_token_payload",
]
