"""
identity/api/routes/auth_cookie_routes.py

Cookie-based аутентификация.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from presentation.rest.dependencies.dependencies import (
    get_account_service,
    get_auth_service,
    get_current_token_payload,
)
from presentation.rest.dependencies.request_meta import RequestMeta, get_request_meta
from presentation.rest.middleware.rate_limit import check_rate_limit
from shared.infrastructure.db.settings import settings

from identity.api.dependencies.auth_dependencies import get_current_account
from identity.api.schemas.auth import AccountResponse, LoginRequest, RegisterRequest
from identity.api.schemas.session import SessionResponse
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.domain.entities.account import Account
from identity.domain.ports.token_service import AccessTokenPayload, ITokenService
from identity.infrastructure.auth.token_service import get_token_service


router: APIRouter = APIRouter(prefix="/auth/cookie", tags=["Auth · Cookie"])

_COOKIE_ACCESS = "access_token"
_COOKIE_REFRESH = "refresh_token"
_IS_PROD = settings.ENVIRONMENT.upper() == "PROD"


# ── Cookie helpers ────────────────────────────────────────────────────────────


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=_COOKIE_ACCESS,
        value=access_token,
        httponly=True,
        secure=_IS_PROD,
        samesite="lax",
        max_age=settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=_COOKIE_REFRESH,
        value=refresh_token,
        httponly=True,
        secure=_IS_PROD,
        samesite="lax",
        max_age=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS * 86400,
        path="/auth/cookie/refresh",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(_COOKIE_ACCESS, path="/")
    response.delete_cookie(_COOKIE_REFRESH, path="/auth/cookie/refresh")


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def cookie_register(
    request: Request,
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> AccountResponse:
    if resp := await check_rate_limit(request, "register"):
        return resp

    account = await service.register(payload.to_command())
    return _account_response(account)


@router.post("/login", status_code=status.HTTP_200_OK)
async def cookie_login(
    request: Request,
    response: Response,
    meta: RequestMeta = Depends(get_request_meta),
    payload: LoginRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    if resp := await check_rate_limit(request, "login"):
        return resp

    cmd = payload.to_command(meta=meta)
    token_pair = await auth_service.login(cmd)
    _set_auth_cookies(response, token_pair.access_token, token_pair.refresh_token)

    ts: ITokenService = get_token_service()
    access_payload = ts.decode_access_token(token_pair.access_token)
    account = await account_service.get_account(access_payload.account_id)
    return _account_response(account)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def cookie_refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    if resp := await check_rate_limit(request, "refresh"):
        return resp

    refresh_token = request.cookies.get(_COOKIE_REFRESH)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh_token cookie missing",
        )

    token_pair = await service.refresh(refresh_token)
    _set_auth_cookies(response, token_pair.access_token, token_pair.refresh_token)
    return {"ok": True}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_logout(
    request: Request,
    response: Response,
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Logout из текущей сессии.
    access_token передаётся сервису для самостоятельного blacklist.
    """
    raw_token = request.cookies.get("access_token") or ""
    await service.logout(
        account_id=token_payload.account_id,
        session_id=token_payload.session_id,
        access_token=raw_token or None,
    )
    _clear_auth_cookies(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_logout_all(
    request: Request,
    response: Response,
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    raw_token = request.cookies.get("access_token") or ""
    await service.logout_all(
        account_id=token_payload.account_id,
        access_token=raw_token or None,
    )
    _clear_auth_cookies(response)


@router.get("/me", status_code=status.HTTP_200_OK)
async def cookie_me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    return _account_response(account)


@router.get("/sessions", status_code=status.HTTP_200_OK)
async def cookie_sessions(
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> list[SessionResponse]:
    sessions = await service.get_sessions(token_payload.account_id)
    return [
        SessionResponse(
            session_id=s.session_id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_current=(s.session_id == token_payload.session_id),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_revoke_session(
    session_id: str,
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.revoke_session(
        account_id=token_payload.account_id,
        session_id=session_id,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _account_response(account: Account) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        email=account.email_str,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_str,
        permissions=sorted(account.permissions),
    )
