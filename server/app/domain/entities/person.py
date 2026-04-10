from dataclasses import dataclass
from uuid import uuid4

from domain.enums import PersonGender
from domain.value_objects.partial_date import PartialDate


@dataclass
class Person:
    id: str
    first_name: str
    last_name: str
    gender: PersonGender
    family_id: str

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None

    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_alive(self) -> bool:
        return self.death_date is None or self.death_date.year is None

    def set_birth_date(self, date: PartialDate) -> None:
        self.birth_date = date

    def set_death_date(self, date: PartialDate) -> None:
        self.death_date = date

    def _validate(self) -> None:
        if not self.id:
            raise ValueError("ID cannot be empty")

        if not self.first_name:
            raise ValueError("First name cannot be empty")

        if not self.last_name:
            raise ValueError("Last name cannot be empty")

        if self.family_id is None:
            raise ValueError("family_id is required")


def create_person(
    first_name: str,
    last_name: str,
    gender: PersonGender,
    family_id: str,
    birth_date: PartialDate | None = None,
    death_date: PartialDate | None = None,
    birth_date_raw: str | None = None,
    death_date_raw: str | None = None,
) -> Person:
    """
    Фабричная функция — единственное место, где генерируется ID.
    Сама доменная модель всегда требует id, но снаружи мы не передаём его при создании.
    """
    return Person(
        id=uuid4().hex,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        family_id=family_id,
        birth_date=birth_date,
        death_date=death_date,
        birth_date_raw=birth_date_raw,
        death_date_raw=death_date_raw,
    )
