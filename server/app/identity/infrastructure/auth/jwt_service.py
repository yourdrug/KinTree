"""
identity/infrastructure/auth/jwt_service.py

JWT и хэш-утилиты.

Алгоритм: HS256. Для genealogy app (single service) — достаточно.
При появлении отдельных сервисов-верификаторов стоит перейти на RS256.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import secrets

import bcrypt
import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from shared.domain.exceptions import AuthenticationError
from shared.infrastructure.db.settings import settings


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise AuthenticationError(
            message="Токен истёк",
            errors={"token": "expired"},
        ) from exc
    except (DecodeError, InvalidTokenError) as exc:
        raise AuthenticationError(
            message="Недействительный токен",
            errors={"token": "invalid"},
        ) from exc


# ── Public API ────────────────────────────────────────────────────────────────


def create_access_token(
    account_id: str,
    email: str,
    role: str,
    session_id: str,
) -> tuple[str, str]:
    """
    Создаёт access token.

    Returns:
        (raw_token, jti) — jti нужен вызывающей стороне для blacklist при logout.
    """
    now = _now_utc()
    jti = secrets.token_hex(16)
    payload = {
        "sub": account_id,
        "email": email,
        "role": role,
        "jti": jti,
        "sid": session_id,  # sid — стандартное имя claim для session id
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES),
    }
    return _encode(payload), jti


def create_refresh_token(account_id: str, session_id: str) -> tuple[str, str]:
    """
    Создаёт refresh token.

    Returns:
        (raw_token, token_hash) — hash хранится в БД, raw отдаётся в куку.
    """
    now = _now_utc()
    raw = secrets.token_hex(32)
    payload = {
        "sub": account_id,
        "sid": session_id,
        "type": REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS),
    }
    # Refresh token — это JWT с подписью + дополнительно хэш хранится в БД
    # JWT-часть позволяет вычитать account_id/session_id без похода в БД
    # hash в БД позволяет инвалидировать конкретный токен
    token = _encode({**payload, "jti": raw})
    token_hash = hash_token(raw)
    return token, token_hash


def decode_access_token(token: str) -> dict:
    payload = _decode(token)
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise AuthenticationError(
            message="Неверный тип токена",
            errors={"token": "wrong_type"},
        )
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = _decode(token)
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise AuthenticationError(
            message="Неверный тип токена",
            errors={"token": "wrong_type"},
        )
    return payload


def hash_token(value: str) -> str:
    """SHA-256 hex. Используется для хранения refresh token в БД."""
    return hashlib.sha256(value.encode()).hexdigest()


def verify_token_hash(raw: str, stored_hash: str) -> bool:
    return secrets.compare_digest(hash_token(raw), stored_hash)


def access_token_ttl_seconds(payload: dict) -> int:
    """Возвращает оставшееся время жизни access token в секундах (для Redis TTL)."""
    now = int(_now_utc().timestamp())
    exp = payload.get("exp", now)
    remaining = exp - now
    return max(remaining, 0)
