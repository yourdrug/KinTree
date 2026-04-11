from abc import abstractmethod

from domain.repositories.base import AbstractRepository


class AbstractFamilyRepository(AbstractRepository):
    @abstractmethod
    async def exists(self, object_id: str) -> bool:
        """Проверяет существование объекта по ID."""
        raise NotImplementedError
