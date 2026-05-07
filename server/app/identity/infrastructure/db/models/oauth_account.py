"""
identity/infrastructure/db/models/oauth_account.py

ORM-модель для таблицы oauth_accounts.
"""

from __future__ import annotations

from shared.infrastructure.db.basemodel import BaseModel
from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class OAuthAccount(BaseModel):
    __tablename__ = "oauth_accounts"

    __table_args__ = (
        # Один провайдер-аккаунт — только один наш аккаунт
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        # Один аккаунт — только одна привязка на провайдера
        UniqueConstraint("account_id", "provider", name="uq_oauth_account_provider"),
        Index("idx_oauth_account_id", "account_id"),
        Index("idx_oauth_provider_lookup", "provider", "provider_user_id"),
    )

    account_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="ID аккаунта владельца",
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Провайдер: google | telegram",
    )
    provider_user_id: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="ID пользователя у провайдера (sub у Google, id у Telegram)",
    )
