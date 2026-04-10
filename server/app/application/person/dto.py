from dataclasses import dataclass
from typing import Optional

from domain.enums import PersonGender
from domain.value_objects.partial_date import PartialDate


@dataclass(frozen=True)
class PatchPersonCommand:
    person_id: str
    update_fields: set[str]

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[PersonGender] = None

    birth_date: Optional[PartialDate] = None
    death_date: Optional[PartialDate] = None
    birth_date_raw: Optional[str] = None
    death_date_raw: Optional[str] = None

@dataclass(frozen=True)
class PutPersonCommand:
    person_id: str

    first_name: str
    last_name: str
    gender: PersonGender

    birth_date: Optional[PartialDate] = None
    death_date: Optional[PartialDate] = None
    birth_date_raw: Optional[str] = None
    death_date_raw: Optional[str] = None
