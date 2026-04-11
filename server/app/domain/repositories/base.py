from abc import ABC, abstractmethod


class AbstractRepository(ABC):
    """
    Базовый контракт репозитория.
    Не знает ничего об инфраструктуре — только о домене.
    """

    @abstractmethod
    async def exists(self, object_id: str) -> bool:
        """Проверяет существование объекта по ID."""
        raise NotImplementedError
