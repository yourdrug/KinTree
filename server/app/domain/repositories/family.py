from __future__ import annotations

from typing import Protocol

from domain.entities.family import Family
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page


class FamilyRepository(Protocol):
    async def get_by_id(self, family_id: str) -> Family:
        """Возвращает семью или бросает NotFoundError."""
        ...

    async def get_by_id_or_none(self, family_id: str) -> Family | None:
        """Возвращает семью или None."""
        ...

    async def list(self, spec: BaseFilterSpec) -> Page[Family]:
        """Список с фильтрацией и пагинацией."""
        ...

    async def save(self, family: Family) -> Family:
        """Создать или обновить. Возвращает сохранённый объект."""
        ...

    async def remove(self, family_id: str) -> None:
        """Удалить по ID."""
        ...

    async def exists(self, family_id: str) -> bool:
        """Проверить существование."""
        ...
