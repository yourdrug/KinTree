"""
api/routes/auth_routes.py
"""

from fastapi import APIRouter, Body, Depends, status
from presentation.rest.dependencies.dependencies import get_auth_service

from identity.api.dependencies.auth_dependencies import get_current_account, get_current_account_id
from identity.api.schemas.auth import (
    AccountResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from identity.application.auth.service import AuthService
from identity.domain.entities.account import Account


router: APIRouter = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> AccountResponse:
    account = await service.register(payload.to_command())
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    token_pair = await service.login(payload.to_command())
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        role=token_pair.role,
        permissions=token_pair.permissions,
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    payload: RefreshRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    token_pair = await service.refresh(payload.refresh_token)
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        role=token_pair.role,
        permissions=token_pair.permissions,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    account_id: str = Depends(get_current_account_id),
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(account_id=account_id)


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )
