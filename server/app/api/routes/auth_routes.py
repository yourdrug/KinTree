"""
api/routes/auth_routes.py

Public auth endpoints and one protected /me endpoint as usage example.
"""

from application.auth.dependencies import get_current_account, get_current_account_id
from application.auth.service import AuthService
from application.dependencies import get_service
from domain.entities.account import Account
from fastapi import APIRouter, Body, Depends, status

from api.schemas.auth import (
    AccountResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)


router: APIRouter = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового аккаунта",
)
async def register(
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_service(AuthService, master=True)),
) -> AccountResponse:
    """
    Создаёт новый аккаунт.
    Возвращает данные аккаунта (без токенов — логин выполняется отдельным запросом).
    """
    account = await service.register(payload.to_command())
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Вход и получение токенов",
)
async def login(
    payload: LoginRequest = Body(...),
    service: AuthService = Depends(get_service(AuthService, master=True)),
) -> TokenResponse:
    """
    Аутентификация по email + пароль.
    Возвращает пару access / refresh токенов.
    """
    token_pair = await service.login(payload.to_command())
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление токенов",
)
async def refresh(
    payload: RefreshRequest = Body(...),
    service: AuthService = Depends(get_service(AuthService, master=True)),
) -> TokenResponse:
    """
    Принимает действующий refresh-токен, инвалидирует его и возвращает новую пару.
    (Refresh token rotation — каждый refresh-токен одноразовый.)
    """
    token_pair = await service.refresh(payload.refresh_token)
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход (инвалидация refresh-токена)",
)
async def logout(
    account_id: str = Depends(get_current_account_id),
    service: AuthService = Depends(get_service(AuthService, master=True)),
) -> None:
    """
    Удаляет refresh-токен из БД.
    Требует действующего access-токена в заголовке Authorization.
    """
    await service.logout(account_id=account_id)
    return None


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Данные текущего аккаунта",
)
async def me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    """
    Возвращает данные аутентифицированного пользователя.
    Требует действующего access-токена в заголовке Authorization.
    """
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
    )
