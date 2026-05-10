"""
identity/api/dependencies/auth_dependencies.py

Зависимости для получения аккаунта из запроса.
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from identity.application.account.service import AccountService
from identity.domain.entities.account import Account
from identity.domain.ports.token_service import AccessTokenPayload, ITokenService
from identity.infrastructure.auth.blacklist_service import is_blacklisted, is_session_blacklisted
from shared.domain.exceptions import AuthenticationError

from presentation.rest.cookies.auth_cookies import get_access_token, get_refresh_token
from presentation.rest.dependencies.services import bearer, get_account_service, get_token_service_dep


def extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """
    Cookie → Bearer. Cookie приоритетнее (браузерные клиенты).
    Единственное место где решается откуда брать токен.
    """
    return get_access_token(request=request) or (credentials.credentials if credentials else None)


async def get_raw_access_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    """
    Dependency: сырая строка access token (cookie или Bearer).

    Raises
        AuthenticationError если токен отсутствует.
    """
    token = extract_token(request, credentials)

    if not token:
        raise AuthenticationError(message="Не авторизован.")

    return token


async def get_raw_refresh_token(request: Request) -> str:
    """
    Dependency: сырая строка refresh token из cookie.
    """

    token = get_refresh_token(request=request)

    if not token:
        raise AuthenticationError(message="Refresh token не передан.")

    return token


async def get_current_token_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    token_service: ITokenService = Depends(get_token_service_dep),
) -> AccessTokenPayload:
    """
    Dependency: полный payload access token как typed VO.

    Работает одинаково для cookie и Bearer авторизации.
    """
    token = extract_token(request, credentials)

    if not token:
        raise AuthenticationError(message="Not authenticated")

    return token_service.decode_access_token(token)


async def get_current_token_payload_verified(
    payload: AccessTokenPayload = Depends(get_current_token_payload),
) -> AccessTokenPayload:
    """
    Dependency: полный payload access token как typed VO.

    Работает одинаково для cookie и Bearer авторизации.

    Проверки:
        1. Токен присутствует (cookie или Authorization header)
        2. Подпись и TTL валидны (decode_access_token)
        3. jti не в Redis blacklist (fail-open при недоступности Redis)

    """

    if payload.jti and await is_blacklisted(payload.jti):
        raise AuthenticationError(
            message="Токен отозван",
            errors={"token": "revoked"},
        )

    if payload.session_id and await is_session_blacklisted(payload.session_id):
        raise AuthenticationError(
            message="Сессия отозвана",
            errors={"token": "session_revoked"},
        )

    return payload


async def get_current_account_id(
    payload: AccessTokenPayload = Depends(get_current_token_payload_verified),
) -> str:
    """
    Dependency: account_id из валидного, не отозванного access_token.

    Работает одинаково для cookie и Bearer авторизации.
    """

    return payload.account_id


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
