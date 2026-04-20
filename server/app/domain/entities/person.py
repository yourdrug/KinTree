"""
domain/entities/person.py

Агрегат Person.

Ключевые решения:
- Person — корень агрегата, хранит все инварианты внутри себя.
- PersonName — Value Object для имени/фамилии.
- PartialDate — Value Object для неполных дат.
- create_person() — единственная фабрика, генерирует ID снаружи агрегата.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import PersonGender
from domain.exceptions import PersonDomainError
from domain.utils import generate_uuid
from domain.value_objects.name import PersonName
from domain.value_objects.partial_date import PartialDate


@dataclass
class Person:
    """
    Агрегат Person.

    Инварианты:
    - name содержит хотя бы first_name или last_name
    - family_id обязателен
    - death_date не раньше birth_date (если оба указаны)
    """

    id: str
    name: PersonName
    gender: PersonGender
    family_id: str

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None

    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    # ── Запросы ──────────────────────────────────────────────────────────────

    @property
    def first_name(self) -> str | None:
        return self.name.first_name

    @property
    def last_name(self) -> str | None:
        return self.name.last_name

    def full_name(self) -> str:
        return self.name.full()

    def is_alive(self) -> bool:
        return self.death_date is None or self.death_date.year is None

    # ── Команды ──────────────────────────────────────────────────────────────

    def update_name(self, first_name: str | None, last_name: str | None) -> None:
        """Обновить имя. PersonName проверит инвариант."""
        self.name = PersonName(first_name=first_name, last_name=last_name)

    def update_birth_date(self, date: PartialDate | None) -> None:
        self.birth_date = date
        self._validate_dates()

    def update_death_date(self, date: PartialDate | None) -> None:
        self.death_date = date
        self._validate_dates()

    # ── Инварианты ───────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.family_id:
            raise PersonDomainError(
                field="family_id",
                message="Человек обязательно должен принадлежать семье.",
            )
        self._validate_dates()

    def _validate_dates(self) -> None:
        if self.birth_date and self.death_date:
            b_year = self.birth_date.year
            d_year = self.death_date.year
            if b_year and d_year and d_year < b_year:
                raise PersonDomainError(
                    field="death_date",
                    message="Дата смерти не может предшествовать дате рождения.",
                )


def create_person(
    gender: PersonGender,
    family_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    birth_date: PartialDate | None = None,
    death_date: PartialDate | None = None,
    birth_date_raw: str | None = None,
    death_date_raw: str | None = None,
) -> Person:
    """
    Фабрика агрегата Person.

    Единственное место где генерируется ID.
    PersonName сразу проверяет инвариант имени.
    """
    return Person(
        id=generate_uuid(),
        name=PersonName(first_name=first_name, last_name=last_name),
        gender=gender,
        family_id=family_id,
        birth_date=birth_date,
        death_date=death_date,
        birth_date_raw=birth_date_raw,
        death_date_raw=death_date_raw,
    )
