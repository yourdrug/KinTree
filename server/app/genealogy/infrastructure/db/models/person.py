from shared.infrastructure.db.basemodel import BaseModel
from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from genealogy.domain.enums import PersonGender


class Person(BaseModel):
    __tablename__: str = "Person"

    __table_args__: tuple = (
        CheckConstraint("birth_month BETWEEN 1 AND 12 OR birth_month IS NULL"),
        CheckConstraint("birth_day BETWEEN 1 AND 31 OR birth_day IS NULL"),
        CheckConstraint("death_month BETWEEN 1 AND 12 OR death_month IS NULL"),
        CheckConstraint("death_day BETWEEN 1 AND 31 OR death_day IS NULL"),
        Index("idx_person_name", "last_name", "first_name"),
        Index("idx_birth_full", "birth_year", "birth_month", "birth_day"),
    )

    first_name: Mapped[str] = mapped_column(
        nullable=True,
        index=True,
    )

    last_name: Mapped[str] = mapped_column(
        nullable=True,
        index=True,
    )

    gender: Mapped[PersonGender] = mapped_column(
        ENUM(
            PersonGender,
            name="person_gender_enum",
        ),
        comment="Gender of the person",
    )

    birth_year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        default=None,
        index=True,
    )

    birth_month: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        default=None,
    )

    birth_day: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        default=None,
    )

    death_year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        default=None,
        index=True,
    )

    death_month: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        default=None,
    )

    death_day: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        default=None,
    )

    birth_date_raw: Mapped[str] = mapped_column(
        String, nullable=True, comment="Original text-date (for example: 'April 1970')"
    )

    death_date_raw: Mapped[str] = mapped_column(
        String, nullable=True, comment="Original text-date (for example: 'April 1970')"
    )

    family_id: Mapped[str] = mapped_column(
        ForeignKey("Family.id", ondelete="CASCADE"),
        comment="Person family ID",
    )
