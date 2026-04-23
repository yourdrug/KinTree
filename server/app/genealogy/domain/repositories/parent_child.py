from typing import Protocol

from genealogy.domain.entities.parent_child import ParentChildRelation


class ParentChildRepository(Protocol):
    """
    Контракт репозитория родительских связей.

    Принципы:
    - Protocol вместо ABC
    - Только доменные сущности
    - Используется для построения графа семьи
    """

    async def get_parents_of(self, person_id: str) -> list[ParentChildRelation]:
        """Все родители данной персоны."""
        ...

    async def get_children_of(self, person_id: str) -> list[ParentChildRelation]:
        """Все дети данной персоны."""
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
