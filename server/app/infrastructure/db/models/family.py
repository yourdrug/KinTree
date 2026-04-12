from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.models.basemodel import BaseModel


class Family(BaseModel):
    __tablename__: str = "Family"

    __table_args__: tuple = (Index("idx_family_name", "name"),)

    name: Mapped[str] = mapped_column(
        nullable=False,
        index=True,
        comment="Family name or branch name",
    )

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("Account.id", ondelete="CASCADE"),
        comment="Family owner account",
    )

    description: Mapped[str] = mapped_column(
        Text,
        default=None,
        nullable=True,
        comment="Description or history of the family",
    )

    origin_place: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="Origin place of the family",
    )

    founded_year: Mapped[int] = mapped_column(
        default=None,
        nullable=True,
        index=True,
        comment="Approximate year when family was founded",
    )

    ended_year: Mapped[int] = mapped_column(
        default=None,
        nullable=True,
        comment="If family line ended",
    )
