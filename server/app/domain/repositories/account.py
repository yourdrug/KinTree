from abc import abstractmethod

from infrastructure.db.models.account import Account

from domain.repositories.base import AbstractRepository


class AbstractAccountRepository(AbstractRepository):
    @abstractmethod
    async def exists(self, object_id: str) -> bool:
        """Проверяет существование объекта по ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, account_id: str) -> Account:
        """Возвращает объект по ID."""
        raise NotImplementedError
