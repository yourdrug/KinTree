"""
identity/infrastructure/auth/token_service.py

Adapter: реализация ITokenService через PyJWT + secrets.

Выделен из jwt_service.py (там были смешаны password hashing и token logic).
Теперь jwt_service.py содержит только этот класс + декодер для зависимостей FastAPI.

Алгоритм: HS256 (symmetric). Для single-service приложения достаточно.
При появлении отдельных сервисов-верификаторов — мигрировать на RS256
путём замены этого адаптера без изменения домена/application.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import secrets

import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from shared.domain.exceptions import AuthenticationError
from shared.infrastructure.db.settings import settings

from identity.domain.ports.token_service import AccessTokenPayload, CreatedTokenPair, ITokenService


_ACCESS_TYPE = "access"
_REFRESH_TYPE = "refresh"


class JWTTokenService:
    """Adapter: JWT-токены через PyJWT."""

    def __init__(self, secret_key: str, access_ttl_minutes: int, refresh_ttl_days: int) -> None:
        self._secret = secret_key
        self._access_ttl = timedelta(minutes=access_ttl_minutes)
        self._refresh_ttl = timedelta(days=refresh_ttl_days)

    # ── Port implementation ───────────────────────────────────────────────────

    def create_token_pair(
        self,
        account_id: str,
        email: str,
        role: str,
        session_id: str,
    ) -> CreatedTokenPair:
        now = datetime.now(tz=settings.tz)

        # Access token
        access_jti = secrets.token_hex(16)
        access_payload = {
            "sub": account_id,
            "email": email,
            "role": role,
            "jti": access_jti,
            "sid": session_id,
            "type": _ACCESS_TYPE,
            "iat": now,
            "exp": now + self._access_ttl,
        }
        access_token = self._encode(access_payload)

        # Refresh token: raw jti хранится в JWT и хэшируется для БД
        raw_refresh_jti = secrets.token_hex(32)
        refresh_payload = {
            "sub": account_id,
            "sid": session_id,
            "jti": raw_refresh_jti,
            "type": _REFRESH_TYPE,
            "iat": now,
            "exp": now + self._refresh_ttl,
        }
        refresh_token = self._encode(refresh_payload)
        refresh_token_hash = self._hash_value(raw_refresh_jti)

        return CreatedTokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=access_jti,
            refresh_token_hash=refresh_token_hash,
        )

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        payload = self._decode(token)
        if payload.get("type") != _ACCESS_TYPE:
            raise AuthenticationError(
                message="Неверный тип токена",
                errors={"token": "wrong_type"},
            )
        return AccessTokenPayload(
            account_id=payload["sub"],
            email=payload.get("email", ""),
            role=payload.get("role", ""),
            jti=payload.get("jti", ""),
            session_id=payload.get("sid", ""),
        )

    def decode_refresh_token(self, token: str) -> dict:
        payload = self._decode(token)
        if payload.get("type") != _REFRESH_TYPE:
            raise AuthenticationError(
                message="Неверный тип токена",
                errors={"token": "wrong_type"},
            )
        return payload

    def verify_token_hash(self, raw_jti: str, stored_hash: str) -> bool:
        return secrets.compare_digest(self._hash_value(raw_jti), stored_hash)

    def get_access_token_ttl(self, token: str) -> int:
        """Оставшееся время жизни в секундах. 0 если истёк."""
        try:
            payload = self._decode(token)
        except AuthenticationError:
            return 0
        now = int(datetime.now(tz=settings.tz).timestamp())
        return max(payload.get("exp", now) - now, 0)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _encode(self, payload: dict) -> str:
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret, algorithms=["HS256"])
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

    @staticmethod
    def _hash_value(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()


_token_service: ITokenService = JWTTokenService(
    secret_key=settings.SECRET_KEY,
    access_ttl_minutes=settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES,
    refresh_ttl_days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS,
)


def get_token_service() -> ITokenService:
    """FastAPI dependency / фабрика. Синглтон — JWTTokenService stateless."""
    return _token_service
