"""
infrastructure/auth/jwt_service.py

JWT и хэш-утилиты. Role вшивается в access-токен как claim.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import secrets

import bcrypt
from domain.exceptions import AuthenticationError
import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from infrastructure.common.settings import settings


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


def create_access_token(account_id: str, email: str, role: str) -> str:
    now = _now_utc()
    payload = {
        "sub": account_id,
        "email": email,
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES),
    }
    return _encode(payload)


def create_refresh_token(account_id: str) -> str:
    now = _now_utc()
    payload = {
        "sub": account_id,
        "jti": secrets.token_hex(32),
        "type": REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS),
    }
    return _encode(payload)


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


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, stored_hash: str) -> bool:
    return secrets.compare_digest(hash_token(token), stored_hash)
