from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from domain.common.filters import BaseFilters
from domain.common.page import Page
from domain.common.sort import BaseSort
from domain.entities.person import Person
from domain.enums import PersonGender
from domain.repositories.base import AbstractRepository


class PersonSortField(StrEnum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"

@dataclass
class PersonFilters(BaseFilters[PersonSortField]):
    family_id: str | None = None
    gender: PersonGender | None = None
    first_name: str | None = None
    last_name: str | None = None

PersonSort = BaseSort[PersonSortField]
PersonPage = Page[Person]


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

    @abstractmethod
    async def get_list(
        self,
        filters: BaseFilters  | None = None,
        limit: int = 20,
        offset: int = 0,
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
