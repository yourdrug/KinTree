"""
identity/domain/ports/token_service.py

Port: интерфейс создания и декодирования токенов.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AccessTokenPayload:
    """Распакованное содержимое access token."""

    account_id: str
    email: str
    role: str
    jti: str
    session_id: str


@dataclass(frozen=True)
class CreatedTokenPair:
    """Результат создания пары токенов."""

    access_token: str
    refresh_token: str
    access_jti: str
    refresh_token_hash: str


class ITokenService(Protocol):
    """Port: управление токенами аутентификации."""

    def create_token_pair(
        self,
        account_id: str,
        email: str,
        role: str,
        session_id: str,
    ) -> CreatedTokenPair:
        """
        Создаёт пару access + refresh токенов для сессии.
        Возвращает токены и метаданные (jti, hash) для сохранения в БД.
        """
        ...

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        """
        Декодирует и валидирует access token.

        Raises:
            AuthenticationError — если токен невалиден или истёк.
        """
        ...

    def decode_refresh_token(self, token: str) -> dict:
        """
        Декодирует и валидирует refresh token.
        Возвращает raw payload (sub, sid, jti, exp).

        Raises:
            AuthenticationError — если токен невалиден или истёк.
        """
        ...

    def verify_token_hash(self, raw_jti: str, stored_hash: str) -> bool:
        """Проверяет что raw_jti совпадает с хэшом из БД."""
        ...

    def get_access_token_ttl(self, token: str) -> int:
        """Возвращает оставшееся время жизни access token в секундах."""
        ...

    def generate_access_hex(self) -> str:
        """Возвращает hex для access token jti"""
        ...

    def generate_refresh_hex(self) -> str:
        """Возвращает hex для refresh token jti"""
        ...

    def generate_session_id_hex(self) -> str:
        """Возвращает hex для session id"""
        ...
