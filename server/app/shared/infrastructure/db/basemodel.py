"""
shared/infrastructure/db/basemodel.py

- BaseModel       — entities с суррогатным PK (id + creation_date)
- LinkedBaseModel — M2M join-таблицы, PK определяется дочерними FK-колонками

Timezone берётся из settings.tz (настраивается через .env TIMEZONE=Europe/Minsk).
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shared.infrastructure.db.settings import settings


class _Base(AsyncAttrs, DeclarativeBase):
    """Единый реестр для всех ORM-моделей."""

    pass


class BaseModel(_Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: uuid4().hex,
        comment="Entity identifier (UUID hex)",
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=settings.tz),
        comment="Timestamp with timezone",
    )


class LinkedBaseModel(_Base):
    """
    База для M2M join-таблиц.
    Без суррогатного id — дочерний класс объявляет составной PK через FK-колонки.
    """

    __abstract__ = True
