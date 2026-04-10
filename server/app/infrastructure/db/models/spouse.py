from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.models.basemodel import BaseModel


class Spouse(BaseModel):
    __tablename__: str = "spouses"

    __table_args__: tuple = (
        # запрет самобрака
        CheckConstraint("first_person_id <> second_person_id"),
        CheckConstraint("first_person_id < second_person_id"),
        Index("idx_spouse_first_person", "first_person_id"),
        Index("idx_spouse_second_person", "second_person_id"),
    )

    first_person_id: Mapped[int] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
    )

    second_person_id: Mapped[int] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
    )

    marriage_year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
    )

    marriage_month: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    marriage_day: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    divorce_year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    marriage_date_raw: Mapped[str] = mapped_column(
        nullable=True,
    )
