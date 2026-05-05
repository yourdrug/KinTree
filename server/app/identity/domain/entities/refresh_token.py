"""
identity/domain/entities/refresh_token.py

Доменная сущность RefreshToken.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shared.domain.utils import generate_uuid


@dataclass
class RefreshToken:
    id: str
    account_id: str
    session_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    revoked: bool = False
    user_agent: str | None = None
    ip_address: str | None = None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def is_active(self, now: datetime) -> bool:
        return not self.revoked and not self.is_expired(now)


def create_refresh_token(
    account_id: str,
    session_id: str,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> RefreshToken:
    return RefreshToken(
        id=generate_uuid(),
        account_id=account_id,
        session_id=session_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=datetime.now(tz=UTC),
        revoked=False,
        user_agent=user_agent,
        ip_address=ip_address,
    )
