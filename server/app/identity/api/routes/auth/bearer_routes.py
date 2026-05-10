"""
identity/api/routes/bearer_routes.py

Bearer-based аутентификация.
"""

from fastapi import APIRouter, Body, Depends, status
from presentation.rest.dependencies.auth import get_raw_access_token
from presentation.rest.dependencies.request_meta import RequestMeta, get_request_meta
from presentation.rest.dependencies.services import get_auth_service

from identity.api.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from identity.application.auth.commands import TokenPair
from identity.application.auth.service import AuthService


router: APIRouter = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    meta: RequestMeta = Depends(get_request_meta),
    payload: LoginRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Авторизация пользователя

    При успешной авторизации возвращаются access и refresh токены, роль права пользователя
    """

    token_pair: TokenPair = await service.login(payload.to_command(meta=meta))
    return TokenResponse.from_command(token_pair=token_pair)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    payload: RefreshRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Обновление refresh_token"""

    token_pair: TokenPair = await service.refresh(payload.refresh_token)
    return TokenResponse.from_command(token_pair=token_pair)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    raw_token: str = Depends(get_raw_access_token),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Logout из текущей сессии."""

    await service.logout(raw_token=raw_token)
