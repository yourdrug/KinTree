"""
domain/repositories/sibling.py

Контракт репозитория сиблинговых связей.
"""

from __future__ import annotations

from typing import Protocol

from genealogy.domain.entities.sibling import SiblingRelation


class SiblingRepository(Protocol):
    async def get_siblings_of(self, person_id: str) -> list[SiblingRelation]:
        """
        Вернуть всех братьев/сестёр персоны с их типом.

        Порядок: FULL → HALF → STEP, внутри группы — по sibling_id.
        """
        ...

    async def get_siblings_of_many(
        self,
        person_ids: list[str],
    ) -> dict[str, list[SiblingRelation]]:
        """
        Batch-вариант: сиблинги для нескольких персон сразу.
        Используется при построении графа семьи.
        Returns: {person_id: [SiblingRelation, ...]}
        """
        ...
