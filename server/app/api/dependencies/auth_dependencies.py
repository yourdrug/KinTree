"""
api/dependencies/auth_dependencies.py

FastAPI dependencies for authentication.

Usage in routes:
    # Require authenticated user — just inject the dependency
    @router.get("/protected")
    async def protected(account: Account = Depends(get_current_account)):
        ...

    # Only need the ID (lighter, no extra DB call)
    @router.delete("/protected")
    async def delete_something(account_id: str = Depends(get_current_account_id)):
        ...

    # Optional auth — endpoint works for both guests and logged-in users
    @router.get("/public")
    async def public(account: Account | None = Depends(get_optional_account)):
        ...
"""

from application.account.service import AccountService
from domain.entities.account import Account
from domain.exceptions import AuthenticationError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from infrastructure.auth.jwt_service import decode_access_token

from api.dependencies.dependencies import get_account_service


# auto_error=False lets us raise a custom AuthenticationError instead of
# FastAPI's generic 403, which keeps our error format consistent.
_bearer = HTTPBearer(auto_error=False)
_bearer_optional = HTTPBearer(auto_error=False)


async def get_current_account_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    Декодирует Bearer-токен и возвращает account_id.
    Бросает AuthenticationError если токен отсутствует или невалиден.
    """
    if credentials is None:
        raise AuthenticationError(
            message="Требуется авторизация",
            errors={"Authorization": "Заголовок отсутствует"},
        )

    payload = decode_access_token(credentials.credentials)
    account_id: str | None = payload.get("sub")

    if not account_id:
        raise AuthenticationError(
            message="Недействительный токен",
            errors={"sub": "Отсутствует идентификатор аккаунта"},
        )

    return account_id


async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    service: AccountService = Depends(get_account_service),
) -> Account:
    """
    Возвращает аутентифицированный аккаунт из БД.
    Бросает AuthenticationError/NotFoundError.
    """
    return await service.get_account(account_id)


async def get_optional_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    service: AccountService = Depends(get_account_service),
) -> Account | None:
    """
    Необязательная аутентификация.
    Возвращает Account если токен валиден, None если токен отсутствует.
    Бросает AuthenticationError если токен присутствует, но невалиден.
    """
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    account_id: str | None = payload.get("sub")
    if not account_id:
        return None

    return await service.get_account(account_id)
