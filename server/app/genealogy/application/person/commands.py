"""
application/person/commands.py

Команды для агрегата Person.

Принципы:
- Команда — это явное намерение изменить состояние системы.
- Все поля входные — нет логики, нет зависимостей.
- UNSET используется в PATCH для различия «не передано» и «передано как None».
- Команды живут в application-слое, не в domain и не в api.
"""

from __future__ import annotations

from dataclasses import dataclass

from genealogy.domain.enums import PersonGender
from genealogy.domain.value_objects.partial_date import PartialDate
from shared.domain.value_objects.unset import UNSET, UnsetType


@dataclass(frozen=True)
class CreatePersonCommand:
    """Создать новую персону."""

    gender: PersonGender
    family_id: str

    first_name: str | None
    last_name: str | None

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None


@dataclass(frozen=True)
class UpdatePersonCommand:
    """
    PUT — полная замена персоны.
    Все поля обязательны, отсутствующий → None.
    """

    person_id: str
    gender: PersonGender

    first_name: str | None
    last_name: str | None

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None


@dataclass(frozen=True)
class PatchPersonCommand:
    """
    PATCH — частичное обновление персоны.
    UNSET = поле не было передано (не трогаем).
    None = поле передано явно как null (сбрасываем).
    """

    person_id: str

    first_name: str | None | UnsetType = UNSET
    last_name: str | None | UnsetType = UNSET
    gender: PersonGender | UnsetType = UNSET

    birth_date: PartialDate | None | UnsetType = UNSET
    death_date: PartialDate | None | UnsetType = UNSET
    birth_date_raw: str | None | UnsetType = UNSET
    death_date_raw: str | None | UnsetType = UNSET
