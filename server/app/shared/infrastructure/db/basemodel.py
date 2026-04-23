"""
infrastructure/db/models/basemodel.py

- BaseModel      → entities with surrogate PK (id + creation_date)
- LinkedBaseModel → M2M join tables, PK defined by child composite FKs
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shared.infrastructure.db.settings import TIMEZONE


class _Base(AsyncAttrs, DeclarativeBase):
    """Single shared registry for all ORM models."""

    pass


class BaseModel(_Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=uuid4().hex,
        comment="Entity identifier (UUID hex)",
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=TIMEZONE),
        comment="UTC creation timestamp",
    )


class LinkedBaseModel(_Base):
    """
    Base for M2M join tables.
    NO surrogate id — child declares composite PK via FK columns.
    """

    __abstract__ = True
