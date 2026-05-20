"""
identity/domain/services/session_service.py

Доменный сервис создания сессий.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from identity.domain.entities.account import Account
from identity.domain.entities.refresh_token import RefreshToken, create_refresh_token
from identity.domain.ports.token_service import CreatedTokenPair, ITokenService


@dataclass(frozen=True)
class CreatedSession:
    """Результат создания сессии — передаётся в application для сохранения."""

    refresh_token: RefreshToken
    access_token: str
    raw_refresh_token: str
    session_id: str


class SessionDomainService:
    """Доменный сервис: создание и ротация сессий."""

    def __init__(self, token_service: ITokenService, refresh_ttl_days: int) -> None:
        self._tokens = token_service
        self._refresh_ttl_days = refresh_ttl_days

    def create_session(
        self,
        account: Account,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> CreatedSession:
        """
        Создать новую сессию для аккаунта.

        Используется при: login, OAuth callback, register (если нужен автологин).
        """
        session_id = self._tokens.generate_session_id_hex()
        return self._build_session(
            account=account,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def rotate_session(
        self,
        account: Account,
        existing_session_id: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> CreatedSession:
        """
        Ротация сессии (refresh token rotation).

        session_id сохраняется — клиент не теряет связь с сессией.
        """
        return self._build_session(
            account=account,
            session_id=existing_session_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def _build_session(
        self,
        account: Account,
        session_id: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> CreatedSession:
        token_pair: CreatedTokenPair = self._tokens.create_token_pair(
            account_id=account.id,
            email=account.email_str,
            role=account.role_str,
            session_id=session_id,
        )

        expires_at = datetime.now(tz=UTC) + timedelta(days=self._refresh_ttl_days)

        refresh_token = create_refresh_token(
            account_id=account.id,
            session_id=session_id,
            token_hash=token_pair.refresh_token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return CreatedSession(
            refresh_token=refresh_token,
            access_token=token_pair.access_token,
            raw_refresh_token=token_pair.refresh_token,
            session_id=session_id,
        )
