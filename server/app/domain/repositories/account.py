from abc import abstractmethod

from domain.entities.account import Account
from domain.repositories.base import AbstractRepository


class AbstractAccountRepository(AbstractRepository):
    @abstractmethod
    async def exists(self, object_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, account_id: str) -> Account:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Account | None:
        """Returns Account or None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, account: Account) -> Account:
        raise NotImplementedError

    @abstractmethod
    async def update_refresh_token(self, account_id: str, hashed_refresh_token: str | None) -> None:
        """Persists a new (or cleared) hashed refresh token."""
        raise NotImplementedError
