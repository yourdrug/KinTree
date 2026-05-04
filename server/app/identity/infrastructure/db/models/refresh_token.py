"""
identity/infrastructure/db/models/refresh_token.py

Таблица refresh_tokens — заменяет поле refresh_token в Account.
"""

from datetime import datetime

from shared.infrastructure.db.basemodel import BaseModel
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    __table_args__ = (
        UniqueConstraint("session_id", name="uq_refresh_token_session"),
        Index("idx_rt_account_id", "account_id"),
        Index("idx_rt_session_id", "session_id"),
    )

    account_id: Mapped[str] = mapped_column(
        ForeignKey("Account.id", ondelete="CASCADE"),
        nullable=False,
        comment="Владелец токена",
    )

    session_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="Уникальный ID сессии, вшивается в access и refresh токены",
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hex от raw refresh token — raw никогда не хранится",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Время истечения токена",
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True = токен отозван (logout или rotation)",
    )

    # Мета для UI списка сессий — не используется в auth-логике
    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="User-Agent браузера/приложения при создании сессии",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP при создании сессии",
    )
