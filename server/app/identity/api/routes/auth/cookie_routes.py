"""
identity/api/routes/cookie_routes.py

Cookie-based аутентификация.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from presentation.rest.cookies.auth_cookies import clear_auth_cookies, get_refresh_token, set_auth_cookies
from presentation.rest.dependencies.auth import get_current_token_payload, get_raw_access_token
from presentation.rest.dependencies.request_meta import RequestMeta, get_request_meta
from presentation.rest.dependencies.services import get_account_service, get_auth_service

from identity.api.schemas.account import AccountResponse
from identity.api.schemas.auth import LoginRequest
from identity.application.account.service import AccountService
from identity.application.auth.commands import LoginCommand, TokenPair
from identity.application.auth.service import AuthService
from identity.domain.entities.account import Account
from identity.domain.ports.token_service import AccessTokenPayload, ITokenService
from identity.infrastructure.auth.token_service import get_token_service


router: APIRouter = APIRouter(prefix="/auth/cookie", tags=["Auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def cookie_login(
    response: Response,
    meta: RequestMeta = Depends(get_request_meta),
    payload: LoginRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: ITokenService = Depends(get_token_service),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """
    Авторизация пользователя

    При успешной авторизации в cookie кладутся токены для удобной работы на клиенте
    """
    command: LoginCommand = payload.to_command(meta=meta)
    token_pair: TokenPair = await auth_service.login(command=command)

    set_auth_cookies(response, token_pair.access_token, token_pair.refresh_token)

    access_payload: AccessTokenPayload = token_service.decode_access_token(token_pair.access_token)
    account: Account = await account_service.get_account(access_payload.account_id)

    return AccountResponse.from_domain(account=account)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def cookie_refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Обновление refresh_token в cookie"""

    refresh_token: str | None = get_refresh_token(request=request)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует refresh_token в cookies",
        )

    token_pair: TokenPair = await service.refresh(refresh_token)
    set_auth_cookies(response, token_pair.access_token, token_pair.refresh_token)

    return {"detail": "refresh_token обновлен."}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_logout(
    response: Response,
    raw_token: str = Depends(get_raw_access_token),
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Logout из текущей сессии."""

    await service.logout(
        session_id=token_payload.session_id,
        access_token=raw_token,
    )
    clear_auth_cookies(response=response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_logout_all(
    response: Response,
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Logout из всех сессий для этого аккаунта."""

    await service.logout_all(account_id=token_payload.account_id)
    clear_auth_cookies(response=response)
