"""
identity/api/routes/auth_cookie_routes.py

Cookie-based аутентификация. Работает параллельно с /auth/* (Bearer-роуты не тронуты).

Куки:
  access_token   httpOnly, Secure*, SameSite=lax, path=/
                 Max-Age = JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60
  refresh_token  httpOnly, Secure*, SameSite=lax, path=/auth/cookie/refresh
                 Max-Age = JWT_TOKEN_REFRESH_LIFETIME_DAYS * 86400

* Secure=False в ENVIRONMENT=DEV — работает на http://localhost без HTTPS.

Фронт токены не видит никогда — они живут только в httpOnly-куках.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from presentation.rest.dependencies.dependencies import get_auth_service, get_account_service

from identity.api.dependencies.auth_dependencies import get_current_account
from identity.api.schemas.auth import AccountResponse, LoginRequest, RegisterRequest
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.domain.entities.account import Account
from identity.infrastructure.auth.jwt_service import decode_access_token
from shared.infrastructure.db.settings import settings


router: APIRouter = APIRouter(prefix="/auth/cookie", tags=["Auth · Cookie"])

# ── Cookie constants ──────────────────────────────────────────────────────────

_COOKIE_ACCESS  = "access_token"
_COOKIE_REFRESH = "refresh_token"
_IS_PROD        = settings.ENVIRONMENT.upper() == "PROD"


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
        path="/auth/cookie/refresh",  # refresh_token доступен только этому роуту
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(_COOKIE_ACCESS,  path="/")
    response.delete_cookie(_COOKIE_REFRESH, path="/auth/cookie/refresh")


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def cookie_register(
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
) -> AccountResponse:
    """
    Регистрация нового аккаунта. Куки не выдаёт — требует отдельного /login.
    """
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
    response: Response,
    payload: LoginRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """
    Логин. Устанавливает httpOnly-куки с токенами.
    Тело ответа — AccountResponse (без токенов).

    account_id извлекается из access_token через decode_access_token,
    т.к. TokenPair не содержит account_id напрямую.
    """
    token_pair = await auth_service.login(payload.to_command())
    _set_auth_cookies(response, token_pair.access_token, token_pair.refresh_token)

    # TokenPair не содержит account_id — читаем из только что созданного access_token
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
    Возвращает { ok: true } — новые токены уходят в куки.
    """
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
    service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Logout: инвалидирует refresh-токен на сервере, удаляет обе куки.
    Работает даже если access_token уже протух — читает sub из refresh_token.
    """
    refresh_token = request.cookies.get(_COOKIE_REFRESH)
    if refresh_token:
        try:
            from identity.infrastructure.auth.jwt_service import decode_refresh_token
            token_payload = decode_refresh_token(refresh_token)
            account_id: str | None = token_payload.get("sub")
            if account_id:
                await service.logout(account_id=account_id)
        except Exception:
            pass  # токен уже невалиден — просто чистим куки

    _clear_auth_cookies(response)


@router.get("/me", status_code=status.HTTP_200_OK)
async def cookie_me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    """
    Возвращает профиль текущего пользователя.
    get_current_account читает access_token из куки через extract_token.
    """
    return AccountResponse(
        id=account.id,
        email=account.email,
        is_verified=account.is_verified,
        is_acc_blocked=account.is_acc_blocked,
        role=account.role_name,
        permissions=sorted(account.permissions),
    )
