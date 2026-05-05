"""
api/routes/auth_routes.py
"""

from fastapi import APIRouter, Body, Depends, status
from presentation.rest.dependencies.dependencies import get_auth_service, get_current_token_payload
from presentation.rest.dependencies.request_meta import RequestMeta, get_request_meta

from identity.api.dependencies.auth_dependencies import get_current_account
from identity.api.schemas.auth import (
    AccountResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from identity.application.auth.service import AuthService
from identity.domain.entities.account import Account
from identity.domain.ports.token_service import AccessTokenPayload


router: APIRouter = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> AccountResponse:
    account = await service.register(payload.to_command())
    return AccountResponse(
        id=account.id,
        email=account.email_str,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    meta: RequestMeta = Depends(get_request_meta),
    payload: LoginRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    token_pair = await service.login(payload.to_command(meta=meta))
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
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(
        account_id=token_payload.account_id,
        session_id=token_payload.session_id,
    )


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        email=account.email_str,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )
