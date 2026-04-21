from typing import Protocol

from domain.entities.spouse import SpouseRelation


class SpouseRepository(Protocol):
    """
    Контракт репозитория супружеских связей.
    """

    async def get_spouses_of(self, person_id: str) -> list[SpouseRelation]:
        """Все браки данной персоны."""
        ...

    async def exists(self, person_a_id: str, person_b_id: str) -> bool:
        """Проверяет существование связи (порядок не важен)."""
        ...

    async def save(self, relation: SpouseRelation) -> SpouseRelation:
        """
        Upsert:
        - create если нет
        - update если есть
        """
        ...

    async def remove(self, person_a_id: str, person_b_id: str) -> None:
        """Удалить связь."""
        ...
