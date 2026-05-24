"""
identity/infrastructure/oauth/google_verifier.py

Верификация Google Authorization Code flow:
  1. Обменять code на токены через token endpoint
  2. Верифицировать id_token через Google JWKS (или introspection)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

import httpx
import jwt
from jwt import PyJWKClient
from shared.infrastructure.db.settings import settings


logger = logging.getLogger(__name__)


_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUER_1 = "https://accounts.google.com"
_GOOGLE_ISSUER_2 = "accounts.google.com"

# Кэшируем JWKS-клиент — он сам обновляет ключи по TTL
_jwks_client = PyJWKClient(_GOOGLE_JWKS_URL, cache_keys=True)


@dataclass(frozen=True)
class GoogleUserInfo:
    """Верифицированные данные пользователя из Google id_token."""

    sub: str  # уникальный ID пользователя в Google
    email: str
    email_verified: bool
    name: str | None
    picture: str | None


async def exchange_code_for_tokens(code: str) -> dict:
    """
    Обменять authorization code на token response от Google.

    Returns:
        dict с ключами: access_token, id_token, token_type, expires_in, ...

    Raises:
        ValueError: если Google вернул ошибку
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )

    data = response.json()

    if "error" in data:
        logger.warning("Google token exchange error: %s — %s", data.get("error"), data.get("error_description"))
        raise ValueError(f"Google OAuth error: {data.get('error_description', data['error'])}")

    return data


def verify_google_id_token(id_token: str) -> GoogleUserInfo:
    """
    Верифицировать Google id_token через JWKS.

    Проверяет:
      - подпись (через публичный ключ Google)
      - aud == GOOGLE_CLIENT_ID
      - iss == accounts.google.com
      - exp (не истёк)

    Returns:
        GoogleUserInfo с данными пользователя

    Raises:
        ValueError: если токен невалиден
    """
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(id_token)
        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID,
            issuer=[_GOOGLE_ISSUER_1, _GOOGLE_ISSUER_2],
            options={"verify_exp": True},
            leeway=timedelta(seconds=30),
        )
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Google id_token истёк") from exc
    except jwt.InvalidAudienceError as exc:
        raise ValueError("Google id_token: неверный audience") from exc
    except jwt.PyJWTError as exc:
        logger.warning("Google id_token verification failed: %s", exc)
        raise ValueError(f"Google id_token невалиден: {exc}") from exc

    email_verified = payload.get("email_verified", False)
    if not email_verified:
        raise ValueError("Email не подтверждён в Google аккаунте")

    return GoogleUserInfo(
        sub=payload["sub"],
        email=payload["email"],
        email_verified=email_verified,
        name=payload.get("name"),
        picture=payload.get("picture"),
    )


async def get_google_user_info(code: str) -> GoogleUserInfo:
    """
    Полный flow: code → tokens → верифицированный GoogleUserInfo.

    Raises:
        ValueError: при любой ошибке верификации
    """
    tokens = await exchange_code_for_tokens(code)
    id_token = tokens.get("id_token")

    if not id_token:
        raise ValueError("Google не вернул id_token")

    return verify_google_id_token(id_token)
