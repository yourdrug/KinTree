from dataclasses import dataclass, field

from domain.enums import PersonGender
from domain.repositories.person import PersonSort, PersonSortField
from domain.value_objects.partial_date import PartialDate
from domain.value_objects.unset import UNSET, UnsetType


@dataclass(frozen=True)
class PatchPersonCommand:
    person_id: str

    gender: PersonGender | UnsetType = UNSET

    first_name: str | None | UnsetType = UNSET
    last_name: str | None | UnsetType = UNSET

    birth_date: PartialDate | None | UnsetType = UNSET
    death_date: PartialDate | None | UnsetType = UNSET
    birth_date_raw: str | None | UnsetType = UNSET
    death_date_raw: str | None | UnsetType = UNSET


@dataclass(frozen=True)
class PutPersonCommand:
    person_id: str

    gender: PersonGender

    first_name: str | None
    last_name: str | None

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None


@dataclass(frozen=True)
class PersonListQuery:
    family_id: str | None = None
    gender: PersonGender | None = None
    first_name: str | None = None
    last_name: str | None = None
    sort: PersonSort = field(default_factory=lambda: PersonSort(PersonSortField.LAST_NAME))
    limit: int = 20
    offset: int = 0
