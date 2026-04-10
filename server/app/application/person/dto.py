from dataclasses import dataclass

from domain.enums import PersonGender
from domain.value_objects.partial_date import PartialDate


@dataclass(frozen=True)
class PatchPersonCommand:
    person_id: str
    update_fields: set[str]

    first_name: str | None = None
    last_name: str | None = None
    gender: PersonGender | None = None

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None


@dataclass(frozen=True)
class PutPersonCommand:
    person_id: str

    first_name: str
    last_name: str
    gender: PersonGender

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None
