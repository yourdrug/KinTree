"""
identity/api/dependencies/auth_dependencies.py

Зависимости для получения аккаунта из запроса.

Логика извлечения и валидации токена живёт в одном месте —
presentation/rest/dependencies/dependencies.py (get_current_account_id, extract_token).
Здесь только доменный слой: превращаем account_id → Account.

Usage in routes:

    # Требует аутентификацию — возвращает полный объект Account из БД
    @router.get("/protected")
    async def protected(account: Account = Depends(get_current_account)):
        ...

    # Необязательная аутентификация — None для гостей
    @router.get("/public")
    async def public(account: Account | None = Depends(get_optional_account)):
        ...

    # Только account_id — без лишнего запроса в БД
    # Импортируйте get_current_account_id напрямую из dependencies.py
    from presentation.rest.dependencies.dependencies import get_current_account_id
"""

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from presentation.rest.dependencies.dependencies import (
    extract_token,
    get_account_service,
    get_current_account_id,
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

    Бросает AuthenticationError если токен невалиден,
    NotFoundError если аккаунт не найден.
    """
    return await service.get_account(account_id)


async def get_optional_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    service: AccountService = Depends(get_account_service),
) -> Account | None:
    """
    Dependency: необязательная аутентификация.

    - Нет токена  → возвращает None (гость)
    - Токен есть, но невалиден → бросает AuthenticationError
    - Токен валиден → возвращает Account из БД
    """
    token = extract_token(request, credentials)
    if not token:
        return None

    payload = decode_access_token(token)
    account_id: str | None = payload.get("sub")
    if not account_id:
        return None

    return await service.get_account(account_id)
