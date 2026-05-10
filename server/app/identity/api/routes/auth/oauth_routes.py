"""
identity/api/routes/auth/oauth_routes.py

OAuth роуты: Google (Authorization Code) + Telegram (Login Widget).

Cookie-версии:
  POST /auth/cookie/oauth/google/callback
  POST /auth/cookie/oauth/telegram/callback
  → кладут токены в cookie, возвращают RedirectResponse на нужную страницу на клиенте
"""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from presentation.rest.cookies.auth_cookies import set_auth_cookies
from presentation.rest.dependencies.request_meta import RequestMeta, get_request_meta
from presentation.rest.dependencies.services import get_oauth_service
from shared.infrastructure.db.settings import settings

from identity.api.schemas.oauth import TelegramCallbackRequest
from identity.application.auth.commands import TokenPair
from identity.application.oauth.commands import GoogleCallbackCommand, TelegramCallbackCommand
from identity.application.oauth.service import OAuthService


router: APIRouter = APIRouter(prefix="/auth/oauth", tags=["Auth"])


@router.get("/google", status_code=status.HTTP_302_FOUND)
async def google_redirect() -> RedirectResponse:
    """
    Шаг 1: редирект пользователя на Google consent screen.

    Параметры:
      - response_type=code   Authorization Code flow
      - scope                запрашиваем email + profile
      - access_type=offline  чтобы получить refresh_token от Google (опционально)
      - prompt=select_account  показать выбор аккаунта даже если уже залогинен
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback", status_code=status.HTTP_200_OK)
async def google_callback_cookie(
    code: str = Query(..., description="Authorization code от Google"),
    meta: RequestMeta = Depends(get_request_meta),
    service: OAuthService = Depends(get_oauth_service),
) -> RedirectResponse:
    """
    Шаг 2: получить code от Google, обменять на токены.

    Google редиректит сюда с ?code=...&state=...
    Кладет токены в Cookie.
    """
    command = GoogleCallbackCommand(
        code=code,
        user_agent=meta.user_agent,
        ip_address=meta.ip_address,
    )
    token_pair: TokenPair = await service.google_callback(command)

    redirect = RedirectResponse(url=settings.FRONTEND_OAUTH_REDIRECT_URL, status_code=302)
    set_auth_cookies(redirect, token_pair.access_token, token_pair.refresh_token)
    return redirect


@router.get("/cookie/telegram/callback", status_code=status.HTTP_200_OK)
async def telegram_callback_cookie(
    id: str = Query(...),
    first_name: str = Query(...),
    auth_date: int = Query(...),
    hash: str = Query(...),
    last_name: str | None = Query(default=None),
    username: str | None = Query(default=None),
    photo_url: str | None = Query(default=None),
    meta: RequestMeta = Depends(get_request_meta),
    service: OAuthService = Depends(get_oauth_service),
) -> RedirectResponse:
    """
    Callback от Telegram Login Widget.

    Telegram редиректит пользователя сюда с GET-параметрами:
        id, first_name, last_name, username, photo_url, auth_date, hash

    Верифицируем HMAC-подпись и выдаём наши токены.
    """
    request_schema = TelegramCallbackRequest(
        id=id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        photo_url=photo_url,
        auth_date=auth_date,
        hash=hash,
    )
    command: TelegramCallbackCommand = request_schema.to_command(meta)
    token_pair: TokenPair = await service.telegram_callback(command)
    redirect = RedirectResponse(url=settings.FRONTEND_OAUTH_REDIRECT_URL, status_code=302)
    set_auth_cookies(redirect, token_pair.access_token, token_pair.refresh_token)
    return redirect
