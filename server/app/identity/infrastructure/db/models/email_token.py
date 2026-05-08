"""
identity/infrastructure/db/models/email_token.py

ORM-модель таблицы email_tokens.

Схема:
  email_tokens — хранит одноразовые токены для верификации email и сброса пароля.

Инварианты на уровне БД:
  - idx_et_account_type_active: быстрый поиск активных токенов по (account_id, token_type).
  - Уникальность токена гарантируется уникальностью token_hash (SHA-256 коллизий нет).
"""

from __future__ import annotations

from datetime import datetime

from shared.infrastructure.db.basemodel import BaseModel
from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column


class EmailToken(BaseModel):
    __tablename__ = "email_tokens"

    __table_args__ = (
        Index("idx_et_token_hash", "token_hash", unique=True),
        Index("idx_et_account_type", "account_id", "token_type"),
    )

    account_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="ID аккаунта владельца токена",
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA-256 hex от raw токена — raw никогда не хранится",
    )

    token_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Тип токена: verify_email | reset_password",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Время истечения токена",
    )

    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True = токен уже был использован (одноразовый)",
    )
