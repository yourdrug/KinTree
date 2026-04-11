from domain.entities.person import Person as DomainPerson
from domain.repositories.person import PersonSortField
from domain.value_objects.partial_date import PartialDate
from sqlalchemy.orm import InstrumentedAttribute

from infrastructure.db.models.person import Person as ORMPerson


class PersonORMMapper:
    @staticmethod
    def to_domain(model: ORMPerson) -> DomainPerson:
        return DomainPerson(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            gender=model.gender,
            family_id=model.family_id,
            birth_date=PersonORMMapper._build_date(
                model.birth_year,
                model.birth_month,
                model.birth_day,
            ),
            death_date=PersonORMMapper._build_date(
                model.death_year,
                model.death_month,
                model.death_day,
            ),
            birth_date_raw=model.birth_date_raw,
            death_date_raw=model.death_date_raw,
        )

    @staticmethod
    def to_persistence(entity: DomainPerson) -> dict:
        return {
            "id": entity.id,
            "first_name": entity.first_name,
            "last_name": entity.last_name,
            "gender": entity.gender,
            "family_id": entity.family_id,
            "birth_year": entity.birth_date.year if entity.birth_date else None,
            "birth_month": entity.birth_date.month if entity.birth_date else None,
            "birth_day": entity.birth_date.day if entity.birth_date else None,
            "death_year": entity.death_date.year if entity.death_date else None,
            "death_month": entity.death_date.month if entity.death_date else None,
            "death_day": entity.death_date.day if entity.death_date else None,
            "birth_date_raw": entity.birth_date_raw,
            "death_date_raw": entity.death_date_raw,
        }

    @staticmethod
    def _build_date(
        year: int | None,
        month: int | None,
        day: int | None,
    ) -> PartialDate | None:
        if year is None and month is None and day is None:
            return None

        return PartialDate(
            year=year,
            month=month,
            day=day,
        )


SORT_COLUMNS: dict[PersonSortField, InstrumentedAttribute] = {
    PersonSortField.FIRST_NAME: ORMPerson.first_name,
    PersonSortField.LAST_NAME: ORMPerson.last_name,
}
