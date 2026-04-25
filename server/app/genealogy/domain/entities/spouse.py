from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from shared.domain.exceptions import RelationDomainError

from genealogy.domain.enums import MarriageStatus


_MIN_YEAR = 1
_MAX_YEAR = 9999
_MIN_MONTH = 1
_MAX_MONTH = 12
_MIN_DAY = 1
_MAX_DAY = 31


@dataclass
class SpouseRelation:
    """
    Value Object: супружеская связь.

    Каноническая форма: first_person_id < second_person_id.
    Используй фабрику create_spouse_relation() — она гарантирует порядок.
    """

    first_person_id: str
    second_person_id: str
    marriage_status: MarriageStatus

    marriage_year: int | None = None
    marriage_month: int | None = None
    marriage_day: int | None = None
    marriage_place: str | None = None
    marriage_date_raw: str | None = None

    divorce_year: int | None = None
    divorce_month: int | None = None
    divorce_day: int | None = None
    divorce_date_raw: str | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpouseRelation):
            return NotImplemented
        return (self.first_person_id, self.second_person_id) == (other.first_person_id, other.second_person_id)

    def __hash__(self) -> int:
        return hash((self.first_person_id, self.second_person_id))

    def __post_init__(self) -> None:
        self._validate()

    def involves(self, person_id: str) -> bool:
        return self.first_person_id == person_id or self.second_person_id == person_id

    def partner_of(self, person_id: str) -> str:
        """Возвращает ID партнёра для данной персоны."""
        if self.first_person_id == person_id:
            return self.second_person_id
        if self.second_person_id == person_id:
            return self.first_person_id
        raise RelationDomainError(field="person_id", message=f"Персона {person_id!r} не участвует в этом браке.")

    def is_active(self) -> bool:
        return self.marriage_status == MarriageStatus.MARRIED

    def divorce(
        self,
        divorce_year: int | None = None,
        divorce_month: int | None = None,
        divorce_day: int | None = None,
        divorce_date_raw: str | None = None,
    ) -> SpouseRelation:
        if self.marriage_status == MarriageStatus.DIVORCED:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"marriage_status": "Эта пара уже разведена."},
            )
        return replace(
            self,
            marriage_status=MarriageStatus.DIVORCED,
            divorce_year=divorce_year,
            divorce_month=divorce_month,
            divorce_day=divorce_day,
            divorce_date_raw=divorce_date_raw,
        )

    def _validate(self) -> None:
        if not self.first_person_id or not self.first_person_id.strip():
            raise RelationDomainError(field="first_person_id", message="ID первого супруга не может быть пустым.")
        if not self.second_person_id or not self.second_person_id.strip():
            raise RelationDomainError(field="second_person_id", message="ID второго супруга не может быть пустым.")
        if self.first_person_id == self.second_person_id:
            raise RelationDomainError(field="ids", message="Человек не может состоять в браке с самим собой.")
        if self.first_person_id > self.second_person_id:
            raise RelationDomainError(
                field="ids",
                message="Используйте фабрику create_spouse_relation() для создания.",
            )
        self._validate_year_field("marriage_year", self.marriage_year)
        self._validate_year_field("divorce_year", self.divorce_year)
        self._validate_month_field("marriage_month", self.marriage_month)
        self._validate_month_field("divorce_month", self.divorce_month)
        self._validate_day_field("marriage_day", self.marriage_day)
        self._validate_day_field("divorce_day", self.divorce_day)
        self._validate_day_requires_month("marriage_day", self.marriage_day, self.marriage_month)
        self._validate_day_requires_month("divorce_day", self.divorce_day, self.divorce_month)
        if self.marriage_year is not None and self.divorce_year is not None and self.divorce_year < self.marriage_year:
            raise RelationDomainError(
                field="divorce_year",
                message="Дата развода не может быть раньше даты свадьбы.",
            )
        if self.marriage_place is not None and len(self.marriage_place.strip()) == 0:
            raise RelationDomainError(
                field="marriage_place",
                message="Место свадьбы не может быть пустой строкой.",
            )
        if self.marriage_date_raw is not None and len(self.marriage_date_raw.strip()) == 0:
            raise RelationDomainError(
                field="marriage_date_raw",
                message="Текстовая дата свадьбы не может быть пустой строкой.",
            )
        if self.divorce_date_raw is not None and len(self.divorce_date_raw.strip()) == 0:
            raise RelationDomainError(
                field="divorce_date_raw",
                message="Текстовая дата развода не может быть пустой строкой.",
            )

    @staticmethod
    def _validate_year_field(field_name: str, value: int | None) -> None:
        if value is not None and not (_MIN_YEAR <= value <= _MAX_YEAR):
            raise RelationDomainError(
                field=field_name,
                message=f"Год должен быть в диапазоне {_MIN_YEAR}–{_MAX_YEAR}.",
            )

    @staticmethod
    def _validate_month_field(field_name: str, value: int | None) -> None:
        if value is not None and not (_MIN_MONTH <= value <= _MAX_MONTH):
            raise RelationDomainError(
                field=field_name,
                message=f"Месяц должен быть в диапазоне {_MIN_MONTH}–{_MAX_MONTH}.",
            )

    @staticmethod
    def _validate_day_field(field_name: str, value: int | None) -> None:
        if value is not None and not (_MIN_DAY <= value <= _MAX_DAY):
            raise RelationDomainError(
                field=field_name,
                message=f"День должен быть в диапазоне {_MIN_DAY}–{_MAX_DAY}.",
            )

    @staticmethod
    def _validate_day_requires_month(day_field: str, day: int | None, month: int | None) -> None:
        if day is not None and month is None:
            raise RelationDomainError(
                field=day_field,
                message="День нельзя указать без месяца.",
            )


def create_spouse_relation(
    person_a_id: str,
    person_b_id: str,
    marriage_status: MarriageStatus = MarriageStatus.MARRIED,
    **kwargs: Any,
) -> SpouseRelation:
    """Фабрика: гарантирует каноническую форму (меньший ID первым)."""
    first, second = sorted([person_a_id, person_b_id])
    return SpouseRelation(
        first_person_id=first,
        second_person_id=second,
        marriage_status=marriage_status,
        **kwargs,
    )
