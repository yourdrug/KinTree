from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from domain.entities.person import Person
from domain.enums import PersonGender
from domain.repositories.base import AbstractRepository


@dataclass
class PersonFilters:
    """
    Фильтры для выборки персон — доменный объект
    """

    family_id: str | None = None
    gender: PersonGender | None = None
    first_name: str | None = None
    last_name: str | None = None
    sort: PersonSort | None = None


class PersonSortField(StrEnum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    BIRTH_DATE = "birth_date"
    CREATED_AT = "created_at"


@dataclass(frozen=True)
class PersonSort:
    field: PersonSortField
    desc: bool = False

    @classmethod
    def from_string(cls, value: str) -> PersonSort:
        """
        Парсит строку вида '-first_name' или 'last_name'.
        Минус в начале означает DESC, без минуса — ASC.
        """
        if value.startswith("-"):
            return cls(field=PersonSortField(value[1:]), desc=True)
        return cls(field=PersonSortField(value), desc=False)


@dataclass
class PersonPage:
    """Результат пагинации."""

    result: list[Person]
    total: int
    limit: int
    offset: int

    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total

    @property
    def has_prev(self) -> bool:
        return self.offset > 0


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
        filters: PersonFilters | None = None,
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
