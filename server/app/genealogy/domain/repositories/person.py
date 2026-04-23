"""
domain/repositories/person.py

Контракт репозитория Person.

Принципы:
- Только протокол (Protocol), без ABC наследования — убирает лишнюю связность.
- Репозиторий работает исключительно с доменными типами.
- Возвращает Page[Person] — обобщённый тип, не зависящий от ORM.
- Методы говорят на языке домена: get_by_id, find_by_family, save, remove.
"""

from __future__ import annotations

from typing import Protocol

from shared.domain.value_objects.pagination import BaseFilterSpec, Page

from genealogy.domain.entities.person import Person


class PersonRepository(Protocol):
    """
    Контракт репозитория персон.

    Protocol вместо ABC:
    - Нет обязательного наследования.
    - Реализация проверяется структурно (duck typing + mypy).
    - Легко мокировать в тестах.
    """

    async def get_by_id(self, person_id: str) -> Person:
        """Возвращает персону или бросает NotFoundError."""
        ...

    async def find_by_family(self, family_id: str) -> list[Person]:
        """Все персоны семьи — используется для проверки инвариантов агрегата."""
        ...

    async def list(self, spec: BaseFilterSpec) -> Page[Person]:
        """Список с фильтрацией и пагинацией."""
        ...

    async def save(self, person: Person) -> Person:
        """Создать или обновить. Возвращает сохранённый объект."""
        ...

    async def remove(self, person_id: str) -> None:
        """Удалить по ID."""
        ...

    async def exists(self, person_id: str) -> bool:
        """Проверить существование."""
        ...
