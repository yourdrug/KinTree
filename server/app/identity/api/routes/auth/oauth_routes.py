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

from identity.application.auth.commands import TokenPair
from identity.application.oauth.service import OAuthService
from identity.infrastructure.oauth.google_provider import GoogleOAuthProvider
from identity.infrastructure.oauth.telegram_provider import TelegramOAuthProvider


router: APIRouter = APIRouter(prefix="/auth/oauth", tags=["Auth"])

# Провайдеры — stateless, создаём один раз
_google_provider = GoogleOAuthProvider()
_telegram_provider = TelegramOAuthProvider()


@router.get("/google", status_code=status.HTTP_302_FOUND)
async def google_redirect() -> RedirectResponse:
    """Шаг 1: редирект на Google consent screen."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code от Google"),
    meta: RequestMeta = Depends(get_request_meta),
    service: OAuthService = Depends(get_oauth_service),
) -> RedirectResponse:
    """Шаг 2: обменять code на токены, положить в cookie."""
    token_pair: TokenPair = await service.handle_callback(
        provider=_google_provider,
        raw_data={"code": code},
        user_agent=meta.user_agent,
        ip_address=meta.ip_address,
    )
    redirect = RedirectResponse(url=settings.FRONTEND_OAUTH_REDIRECT_URL, status_code=302)
    set_auth_cookies(redirect, token_pair.access_token, token_pair.refresh_token)
    return redirect


@router.get("/cookie/telegram/callback")
async def telegram_callback(
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
    """Callback от Telegram Login Widget."""
    token_pair: TokenPair = await service.handle_callback(
        provider=_telegram_provider,
        raw_data={
            "id": id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "photo_url": photo_url,
            "auth_date": auth_date,
            "hash": hash,
        },
        user_agent=meta.user_agent,
        ip_address=meta.ip_address,
    )
    redirect = RedirectResponse(url=settings.FRONTEND_OAUTH_REDIRECT_URL, status_code=302)
    set_auth_cookies(redirect, token_pair.access_token, token_pair.refresh_token)
    return redirect
