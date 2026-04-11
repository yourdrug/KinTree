from dataclasses import dataclass

from domain.enums import PersonGender
from domain.exceptions import DomainPersonError
from domain.utils import generate_uuid
from domain.value_objects.partial_date import PartialDate


@dataclass
class Person:
    id: str
    gender: PersonGender
    family_id: str

    first_name: str | None = None
    last_name: str | None = None

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None

    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name]))

    def is_alive(self) -> bool:
        return self.death_date is None or self.death_date.year is None

    def set_birth_date(self, date: PartialDate) -> None:
        self.birth_date = date

    def set_death_date(self, date: PartialDate) -> None:
        self.death_date = date

    def _validate(self) -> None:
        if not self.first_name and not self.last_name:
            raise DomainPersonError(
                message="Ошибка валидации",
                errors={"first_name": "Как минимум одно из двух полей (фамилия или имя) должно быть заполнено."},
            )

        if self.family_id is None:
            raise DomainPersonError(
                message="Ошибка валидации", errors={"family_id": "Человек обязательно должен принадлежать семье."}
            )

        if self.birth_date and self.death_date:
            if self.birth_date.year and self.death_date.year and self.death_date.year < self.birth_date.year:
                raise DomainPersonError(
                    message="Ошибка валидации",
                    errors={"birth_date": "Дата смерти не может предшествовать дате рождения."},
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
    Фабричная функция — единственное место, где генерируется ID.
    Сама доменная модель всегда требует id, но снаружи мы не передаём его при создании.
    """
    return Person(
        id=generate_uuid(),
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        family_id=family_id,
        birth_date=birth_date,
        death_date=death_date,
        birth_date_raw=birth_date_raw,
        death_date_raw=death_date_raw,
    )
