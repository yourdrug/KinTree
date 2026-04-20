from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from domain.enums import MarriageStatus
from domain.exceptions import RelationDomainError


@dataclass(frozen=True)
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
        return replace(
            self,
            marriage_status=MarriageStatus.DIVORCED,
            divorce_year=divorce_year,
            divorce_month=divorce_month,
            divorce_day=divorce_day,
            divorce_date_raw=divorce_date_raw,
        )

    def _validate(self) -> None:
        if not self.first_person_id or not self.second_person_id:
            raise RelationDomainError(field="ids", message="ID супругов не могут быть пустыми.")
        if self.first_person_id == self.second_person_id:
            raise RelationDomainError(field="ids", message="Человек не может состоять в браке с самим собой.")
        if self.first_person_id > self.second_person_id:
            raise RelationDomainError(
                field="ids",
                message="Используйте фабрику create_spouse_relation() для создания.",
            )
        if self.marriage_year is not None and self.divorce_year is not None and self.divorce_year < self.marriage_year:
            raise RelationDomainError(
                field="divorce_year",
                message="Дата развода не может быть раньше даты свадьбы.",
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
