"""
Spouse: супружеская связь между двумя персонами.

Решения по схеме:
- Составной PK (first_person_id, second_person_id) — гарантирует уникальность пары.
- CheckConstraint first_person_id < second_person_id — каноническая форма,
  гарантирует что пара (A,B) и (B,A) — это одна запись, а не две.
- marriage_status: MARRIED | DIVORCED | WIDOWED — текущий статус.
- Полные даты свадьбы и развода: year+month+day каждая, плюс raw-поле
  для хранения оригинальной записи ("лето 1965", "ок. 1940").
- divorce_year добавлен вместо отдельной таблицы — развод это атрибут брака.

Поля которые убраны:
- суррогатный id — не нужен, пара уникальна по двум FK
- creation_date — есть в LinkedBaseModel через updated_at если нужно,
  но для связи дата брака важнее даты создания записи

Поля которые добавлены:
- marriage_month, marriage_day — были только year
- divorce_month, divorce_day  — были только year
- marriage_status             — явный статус вместо "есть divorce_year или нет"
- updated_at                  — когда последний раз редактировали запись
"""

from datetime import datetime

from shared.infrastructure.db.basemodel import LinkedBaseModel
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from genealogy.domain.enums import MarriageStatus


class Spouse(LinkedBaseModel):
    __tablename__: str = "spouses"

    __table_args__: tuple = (
        # Запрет самобрака
        CheckConstraint(
            "first_person_id <> second_person_id",
            name="ck_spouse_no_self",
        ),
        # Каноническая форма: меньший ID всегда первый
        # Это гарантирует что (A,B) и (B,A) — одна запись
        CheckConstraint(
            "first_person_id < second_person_id",
            name="ck_spouse_canonical_order",
        ),
        # Развод не может быть раньше свадьбы (если оба года заданы)
        CheckConstraint(
            "divorce_year IS NULL OR marriage_year IS NULL OR divorce_year >= marriage_year",
            name="ck_spouse_divorce_after_marriage",
        ),
        Index("idx_spouse_first", "first_person_id"),
        Index("idx_spouse_second", "second_person_id"),
        # Составной индекс для поиска конкретной пары
        Index("idx_spouse_pair", "first_person_id", "second_person_id", unique=True),
    )

    first_person_id: Mapped[str] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID первого супруга (меньший из двух по значению)",
    )

    second_person_id: Mapped[str] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID второго супруга (больший из двух по значению)",
    )

    marriage_status: Mapped[MarriageStatus] = mapped_column(
        ENUM(MarriageStatus, name="marriage_status_enum"),
        nullable=False,
        default=MarriageStatus.MARRIED,
        comment="Текущий статус: MARRIED | DIVORCED | WIDOWED",
    )

    marriage_year: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
        comment="Год бракосочетания",
    )

    marriage_month: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Месяц бракосочетания (1–12)",
    )

    marriage_day: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="День бракосочетания (1–31)",
    )

    marriage_place: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Место бракосочетания",
    )

    marriage_date_raw: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Оригинальная запись даты свадьбы: 'лето 1965', 'ок. 1940'",
    )

    divorce_year: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Год развода",
    )

    divorce_month: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Месяц развода (1–12)",
    )

    divorce_day: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="День развода (1–31)",
    )

    divorce_date_raw: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Оригинальная запись даты развода",
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последнего обновления записи",
    )
