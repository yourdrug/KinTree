from sqlalchemy import (
    Column, BigInteger, String, SmallInteger, DateTime, ForeignKey, CheckConstraint, Index
)
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from domain.models.basemodel import BaseModel


class Person(BaseModel):
    __tablename__ = "Person"

    first_name: Mapped[str] = mapped_column(
        index=True,
    )
    last_name: Mapped[str] = mapped_column(
        index=True,
    )

    gender = Column(SmallInteger)

    birth_year: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    birth_month: Mapped[int | None] = mapped_column(SmallInteger)
    birth_day: Mapped[int | None] = mapped_column(SmallInteger)

    death_year: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    death_month: Mapped[int | None] = mapped_column(SmallInteger)
    death_day: Mapped[int | None] = mapped_column(SmallInteger)

    birth_date_raw: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Original text-date (for example: 'April 1970')"
    )

    death_date_raw: Mapped[str | None] = mapped_column(String, nullable=True)


    __table_args__ = (
        CheckConstraint("birth_month BETWEEN 1 AND 12 OR birth_month IS NULL"),
        CheckConstraint("birth_day BETWEEN 1 AND 31 OR birth_day IS NULL"),
        CheckConstraint("death_month BETWEEN 1 AND 12 OR death_month IS NULL"),
        CheckConstraint("death_day BETWEEN 1 AND 31 OR death_day IS NULL"),

        Index("idx_person_name", "last_name", "first_name"),
        Index("idx_birth_full", "birth_year", "birth_month", "birth_day"),
    )
