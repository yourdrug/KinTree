"""
identity/api/routes/auth_cookie_routes.py

Cookie-based аутентификация для KinTree.

Что изменилось относительно оригинала:
  - login передаёт user_agent и ip для мета-данных сессии
  - logout читает payload из access token → blacklist jti + revoke session
  - logout-all — новый эндпоинт (выход со всех устройств)
  - /sessions — список активных сессий
  - /sessions/{session_id} DELETE — revoke конкретной сессии
  - Rate limiting на login, refresh, register

Куки:
  access_token   httpOnly, Secure*, SameSite=lax, path=/
  refresh_token  httpOnly, Secure*, SameSite=lax, path=/auth/cookie/refresh

* Secure=False в ENVIRONMENT=DEV.

SameSite=lax выбран вместо strict потому что KinTree может открываться
по ссылкам (например, поделиться деревом) — strict блокирует куки при
переходе с внешнего сайта, lax разрешает GET-переходы.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from presentation.rest.dependencies.dependencies import (
    get_account_service,
    get_auth_service,
    get_current_token_payload,
)
from presentation.rest.middleware.rate_limit import check_rate_limit
from shared.infrastructure.db.settings import settings

from identity.api.dependencies.auth_dependencies import get_current_account
from identity.api.schemas.auth import AccountResponse, LoginRequest, RegisterRequest
from identity.api.schemas.session import SessionResponse
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.domain.entities.account import Account


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


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def cookie_register(
    request: Request,
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> AccountResponse:
    """Регистрация. Куки не выдаёт — требует отдельного /login."""
    if resp := await check_rate_limit(request, "register"):
        return resp

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
async def cookie_login(
    request: Request,
    response: Response,
    payload: LoginRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """
    Логин. Устанавливает httpOnly-куки.
    Возвращает AccountResponse (токены клиент не видит).
    """
    if resp := await check_rate_limit(request, "login"):
        return resp

    from identity.application.auth.service import LoginCommand

    cmd = LoginCommand(
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("User-Agent"),
        ip_address=_get_client_ip(request),
    )
    token_pair = await auth_service.login(cmd)
    _set_auth_cookies(response, token_pair.access_token, token_pair.refresh_token)

    from identity.infrastructure.auth.jwt_service import decode_access_token

    token_payload = decode_access_token(token_pair.access_token)
    account_id: str = token_payload["sub"]

    account = await account_service.get_account(account_id)
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def cookie_refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Обновляет пару токенов через refresh_token из куки.
    Token rotation: старый refresh revoke, выдаётся новый.
    """
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
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Logout из текущей сессии.

    - jti access token → Redis blacklist (токен становится невалидным немедленно)
    - session_id → revoke refresh token в БД
    - Куки удаляются

    Работает даже если access token уже протух: get_current_token_payload
    поймает ошибку, и мы чистим куки без blacklist.
    """
    account_id: str = token_payload.get("sub", "")
    session_id: str | None = token_payload.get("sid")

    await service.logout(
        account_id=account_id,
        session_id=session_id,
        access_token_payload=token_payload,
    )
    _clear_auth_cookies(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_logout_all(
    response: Response,
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Logout со всех устройств.
    Отзывает все refresh tokens аккаунта, текущий access → blacklist.
    """
    account_id: str = token_payload.get("sub", "")
    await service.logout_all(
        account_id=account_id,
        access_token_payload=token_payload,
    )
    _clear_auth_cookies(response)


@router.get("/me", status_code=status.HTTP_200_OK)
async def cookie_me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    """Профиль текущего пользователя."""
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )


@router.get("/sessions", status_code=status.HTTP_200_OK)
async def cookie_sessions(
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> list[SessionResponse]:
    """
    Список активных сессий аккаунта.
    Позволяет пользователю видеть, с каких устройств он залогинен.
    """
    account_id: str = token_payload.get("sub", "")
    current_sid: str = token_payload.get("sid", "")
    sessions = await service.get_sessions(account_id)

    return [
        SessionResponse(
            session_id=s.session_id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_current=(s.session_id == current_sid),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cookie_revoke_session(
    session_id: str,
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Отзывает конкретную сессию (например, выйти с телефона).
    Нельзя удалить чужую сессию — проверяется account_id.
    """
    account_id: str = token_payload.get("sub", "")
    await service.revoke_session(account_id=account_id, session_id=session_id)
