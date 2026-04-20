from __future__ import annotations

from typing import Protocol

from domain.entities.parent_child import ParentChildRelation
from domain.entities.spouse import SpouseRelation


class ParentChildRepository(Protocol):
    """
    Контракт репозитория родительских связей.

    Принципы:
    - Protocol вместо ABC
    - Только доменные сущности
    - Используется для построения графа семьи
    """

    async def get_by_family(self, family_id: str) -> list[ParentChildRelation]:
        """Все родительские связи в семье."""
        ...

    async def get_parents_of(self, person_id: str) -> list[ParentChildRelation]:
        """Все родители данной персоны."""
        ...

    async def get_children_of(self, person_id: str) -> list[ParentChildRelation]:
        """Все дети данной персоны."""
        ...

    async def get_all_for_persons(self, person_ids: list[str]) -> list[ParentChildRelation]:
        """Все связи, где участвует хотя бы одна персона."""
        ...

    async def exists(self, parent_id: str, child_id: str) -> bool:
        """Проверяет существование связи."""
        ...

    async def save(self, relation: ParentChildRelation) -> ParentChildRelation:
        """
        Создать связь.

        (Можно оставить create, но save консистентнее с PersonRepository)
        """
        ...

    async def remove(self, parent_id: str, child_id: str) -> None:
        """Удалить связь."""
        ...


class SpouseRepository(Protocol):
    """
    Контракт репозитория супружеских связей.
    """

    async def get_by_family(self, family_id: str) -> list[SpouseRelation]:
        """Все супружеские связи в семье."""
        ...

    async def get_spouses_of(self, person_id: str) -> list[SpouseRelation]:
        """Все браки данной персоны."""
        ...

    async def get_all_for_persons(self, person_ids: list[str]) -> list[SpouseRelation]:
        """Все связи, где участвует хотя бы одна персона."""
        ...

    async def exists(self, person_a_id: str, person_b_id: str) -> bool:
        """Проверяет существование связи (порядок не важен)."""
        ...

    async def save(self, relation: SpouseRelation) -> SpouseRelation:
        """
        Upsert:
        - create если нет
        - update если есть
        """
        ...

    async def remove(self, person_a_id: str, person_b_id: str) -> None:
        """Удалить связь."""
        ...
