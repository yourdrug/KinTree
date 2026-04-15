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

from collections.abc import AsyncGenerator

from application.account.service import AccountService
from domain.entities.account import Account
from domain.exceptions import AuthenticationError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from infrastructure.auth.jwt_service import decode_access_token
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.base_dependencies import get_asession, get_service

# auto_error=False lets us raise a custom AuthenticationError instead of
# FastAPI's generic 403, which keeps our error format consistent.
_bearer = HTTPBearer(auto_error=False)
_bearer_optional = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_account_id(credentials: HTTPAuthorizationCredentials | None) -> str:
    # TODO ref in auth service
    """
    Decode the bearer token and return the account_id (sub claim).
    Raises AuthenticationError on any problem.
    """
    if credentials is None:
        raise AuthenticationError(
            message="Требуется авторизация",
            errors={"Authorization": "Заголовок отсутствует"},
        )

    payload = decode_access_token(credentials.credentials)  # raises on expired / invalid

    account_id: str | None = payload.get("sub")
    if not account_id:
        raise AuthenticationError(
            message="Недействительный токен",
            errors={"sub": "Отсутствует идентификатор аккаунта"},
        )

    return account_id


async def _get_session_from_factory() -> AsyncGenerator[AsyncSession, None]:
    """Thin wrapper so auth deps get their own session, independent of route sessions."""
    session_factory = get_asession(master=False)
    async for session in session_factory():
        yield session


# ---------------------------------------------------------------------------
# Public dependencies
# ---------------------------------------------------------------------------


async def get_current_account_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    Require a valid access token.

    Returns the account_id string.
    Raises 401 AuthenticationError when the token is missing, expired, or malformed.
    """
    return _extract_account_id(credentials)


async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    service: AccountService = Depends(get_service(AccountService, master=False)),
) -> Account:
    """
    Require a valid access token AND a matching account in the database.

    Returns the full Account domain entity.
    Raises 401 if token is invalid, 404 if the account no longer exists.
    """
    account: Account = await service.get_account(
        account_id=account_id,
    )
    return account


async def get_optional_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    service: AccountService = Depends(get_service(AccountService, master=False)),
) -> Account | None:
    """
    Optional authentication — does NOT raise if no token is supplied.

    Returns the Account if a valid token is present, None otherwise.
    Still raises 401 if a token IS provided but is invalid/expired,
    so clients cannot silently pass broken tokens.
    """
    if credentials is None:
        return None

    account_id = _extract_account_id(credentials)

    account: Account = await service.get_account(
        account_id=account_id,
    )
    return account
