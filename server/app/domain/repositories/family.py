from abc import abstractmethod

from domain.entities.family import Family
from domain.repositories.base import AbstractRepository


class AbstractFamilyRepository(AbstractRepository):
    @abstractmethod
    async def exists(self, object_id: str) -> bool:
        """Проверяет существование объекта по ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, family_id: str) -> Family:
        """
        Возвращает семью по ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, family: Family) -> Family:
        """Создаёт семью и возвращает её с заполненными полями из БД."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, family: Family) -> Family:
        """Обновляет семью целиком и возвращает обновлённую версию."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, family_id: str) -> None:
        """Удаляет семью по ID."""
        raise NotImplementedError
