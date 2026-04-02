from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from infrastructure.common.settings import TIMEZONE
from infrastructure.common.utils import generate_uuid


class BaseModel(AsyncAttrs, DeclarativeBase):
    """
    BaseModel: Abstract base model for all database entities.
    Provides common columns and configuration that will be inherited by all models.
    """

    __abstract__: bool = True  # Marks this as abstract base class (no table will be created)

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=generate_uuid,
        comment='Identifier of the entity',
    )

    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=TIMEZONE),
        comment='Entity creation date',
    )
