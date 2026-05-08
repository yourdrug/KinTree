"""
identity/domain/entities/email_token.py

EmailToken — Entity для одноразовых email-токенов.

Используется для:
  - Подтверждения email после регистрации (verify_email)
  - Сброса пароля (reset_password)

Принципы:
  - Токен одноразовый: использование → is_used=True.
  - Токен имеет TTL: expires_at.
  - Только один активный токен на (account_id, token_type) — инвариант на уровне БД.
  - Сам токен хранится как SHA-256 hex (аналогично refresh_token).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from shared.domain.utils import generate_uuid


class EmailTokenType(StrEnum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"


@dataclass
class EmailToken:
    id: str
    account_id: str
    token_hash: str  # SHA-256 hex от raw токена — raw никогда не хранится
    token_type: EmailTokenType
    expires_at: datetime
    created_at: datetime
    is_used: bool = False

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(tz=UTC)
        return now >= self.expires_at

    def is_valid(self, now: datetime | None = None) -> bool:
        return not self.is_used and not self.is_expired(now)


def create_email_token(
    account_id: str,
    token_hash: str,
    token_type: EmailTokenType,
    expires_at: datetime,
) -> EmailToken:
    """Фабрика EmailToken. Генерирует id."""
    return EmailToken(
        id=generate_uuid(),
        account_id=account_id,
        token_hash=token_hash,
        token_type=token_type,
        expires_at=expires_at,
        created_at=datetime.now(tz=UTC),
        is_used=False,
    )
