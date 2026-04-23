"""
infrastructure/person/mapper.py

Маппер Person: ORM ↔ Domain.

Принципы:
- Маппер — чистый объект без состояния (можно сделать @staticmethod).
- to_domain() всегда строит Value Objects через их конструкторы.
- to_persistence() возвращает dict — не зависит от конкретного ORM-метода.
- Нет условий, нет бизнес-логики — только трансформация данных.
"""

from __future__ import annotations

from genealogy.domain.entities.person import Person
from genealogy.domain.value_objects.family_ref import FamilyRef
from genealogy.domain.value_objects.partial_date import PartialDate
from genealogy.domain.value_objects.person_name import PersonName
from genealogy.infrastructure.db.models.person import Person as ORMPerson


class PersonMapper:
    """Трансформирует Person между ORM-слоем и доменным слоем."""

    @staticmethod
    def to_domain(model: ORMPerson) -> Person:
        return Person(
            id=model.id,
            name=PersonName(
                first_name=model.first_name,
                last_name=model.last_name,
            ),
            gender=model.gender,
            family_ref=FamilyRef(family_id=model.family_id),
            birth_date=PersonMapper._build_date(model.birth_year, model.birth_month, model.birth_day),
            death_date=PersonMapper._build_date(model.death_year, model.death_month, model.death_day),
            birth_date_raw=model.birth_date_raw,
            death_date_raw=model.death_date_raw,
        )

    @staticmethod
    def to_persistence(person: Person) -> dict:
        return {
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "gender": person.gender,
            "family_id": person.family_id,
            "birth_year": person.birth_date.year if person.birth_date else None,
            "birth_month": person.birth_date.month if person.birth_date else None,
            "birth_day": person.birth_date.day if person.birth_date else None,
            "death_year": person.death_date.year if person.death_date else None,
            "death_month": person.death_date.month if person.death_date else None,
            "death_day": person.death_date.day if person.death_date else None,
            "birth_date_raw": person.birth_date_raw,
            "death_date_raw": person.death_date_raw,
        }

    @staticmethod
    def _build_date(
        year: int | None,
        month: int | None,
        day: int | None,
    ) -> PartialDate | None:
        if year is None and month is None and day is None:
            return None
        return PartialDate(year=year, month=month, day=day)
