from shared.infrastructure.db.basemodel import BaseModel
from sqlalchemy import ForeignKey, Index, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column


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

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="is public Family",
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
