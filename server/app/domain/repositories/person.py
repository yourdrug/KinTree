from __future__ import annotations

from abc import abstractmethod

from domain.entities.person import Person
from domain.filters.base import BaseFilterSpec
from domain.filters.page import PersonPage
from domain.repositories.base import AbstractRepository


class AbstractPersonRepository(AbstractRepository):
    """
    Контракт репозитория персон.

    Живёт в домене — сервис зависит только от этого интерфейса,
    не от конкретной реализации с SQLAlchemy.
    """

    @abstractmethod
    async def exists(self, object_id: str) -> bool:
        """Проверяет существование объекта по ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, person_id: str) -> Person:
        """
        Возвращает персону по ID.
        Бросает PersonNotFoundError если не найдена.
        """
        raise NotImplementedError

    # TODO get_by_id_or_None

    @abstractmethod
    async def get_list(
        self,
        filters: BaseFilterSpec,
    ) -> PersonPage:
        """Возвращает список персон с фильтрацией и пагинацией."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, person: Person) -> Person:
        """Создаёт персону и возвращает её с заполненными полями из БД."""
        raise NotImplementedError

    @abstractmethod
    async def get_persons_by_family(self, family_id: str) -> list[Person]:
        """Создаёт персону и возвращает её с заполненными полями из БД."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, person: Person) -> Person:
        """Обновляет персону целиком и возвращает обновлённую версию."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, person_id: str) -> None:
        """Удаляет персону по ID."""
        raise NotImplementedError
