from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.parent_child import ParentChildRelation
from domain.entities.spouse import SpouseRelation


class AbstractParentChildRepository(ABC):
    @abstractmethod
    async def get_by_family(self, family_id: str) -> list[ParentChildRelation]:
        """Все родительские связи в семье."""
        raise NotImplementedError

    @abstractmethod
    async def get_parents_of(self, person_id: str) -> list[ParentChildRelation]:
        """Все родители данной персоны."""
        raise NotImplementedError

    @abstractmethod
    async def get_children_of(self, person_id: str) -> list[ParentChildRelation]:
        """Все дети данной персоны."""
        raise NotImplementedError

    @abstractmethod
    async def get_all_for_persons(self, person_ids: list[str]) -> list[ParentChildRelation]:
        """
        Все родительские связи где участвует хотя бы одна из персон.
        Используется для построения графа семьи.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, parent_id: str, child_id: str) -> bool:
        """Проверяет существование конкретной связи."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, relation: ParentChildRelation) -> ParentChildRelation:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, parent_id: str, child_id: str) -> None:
        raise NotImplementedError


class AbstractSpouseRepository(ABC):
    @abstractmethod
    async def get_by_family(self, family_id: str) -> list[SpouseRelation]:
        """Все супружеские связи в семье."""
        raise NotImplementedError

    @abstractmethod
    async def get_spouses_of(self, person_id: str) -> list[SpouseRelation]:
        """Все браки данной персоны."""
        raise NotImplementedError

    @abstractmethod
    async def get_all_for_persons(self, person_ids: list[str]) -> list[SpouseRelation]:
        """
        Все супружеские связи где участвует хотя бы одна из персон.
        Используется для построения графа семьи.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, person_a_id: str, person_b_id: str) -> bool:
        """Проверяет существование связи (не зависит от порядка ID)."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, relation: SpouseRelation) -> SpouseRelation:
        raise NotImplementedError

    @abstractmethod
    async def update(self, relation: SpouseRelation) -> SpouseRelation:
        """Обновление статуса (развод, вдовство)."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, person_a_id: str, person_b_id: str) -> None:
        raise NotImplementedError
