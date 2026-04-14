"""
api/auth/dependencies.py

FastAPI dependencies for authentication.
Import get_current_account wherever a route needs an authenticated user.
"""

from domain.entities.account import Account
from domain.exceptions import AuthenticationError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from infrastructure.account.repositories import AccountRepository
from infrastructure.auth.jwt_service import decode_access_token
from sqlalchemy.ext.asyncio import AsyncSession

from application.dependencies import get_asession


# HTTPBearer extracts the token from the Authorization: Bearer <token> header.
# auto_error=False lets us raise a custom 401 instead of FastAPI's default.
_bearer = HTTPBearer(auto_error=False)


async def get_current_account_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    Validates the access token and returns the account_id (sub claim).
    Raises AuthenticationError (→ 401) when:
      - No Authorization header present
      - Token is expired or malformed
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
    asession: AsyncSession = Depends(get_asession(master=False)),
) -> Account:
    """
    Resolves the full Account domain entity from the token's sub claim.
    Useful when routes need account data beyond just the ID.
    """

    repo = AccountRepository(asession)
    return await repo.get_by_id(account_id)
