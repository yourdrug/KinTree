from fastapi import Request, Response
from shared.infrastructure.db.settings import settings


_COOKIE_ACCESS = "access_token"
_COOKIE_REFRESH = "refresh_token"
_IS_PROD = settings.ENVIRONMENT.upper() == "PROD"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
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


def get_refresh_token(request: Request) -> str | None:
    refresh_token: str | None = request.cookies.get(_COOKIE_REFRESH)
    return refresh_token


def get_access_token(request: Request) -> str | None:
    access_token: str | None = request.cookies.get(_COOKIE_ACCESS)
    return access_token


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(_COOKIE_ACCESS, path="/")
    response.delete_cookie(_COOKIE_REFRESH, path="/auth/cookie/refresh")
