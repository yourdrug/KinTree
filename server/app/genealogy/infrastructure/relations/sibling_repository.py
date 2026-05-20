"""
infrastructure/relations/sibling_repository.py

SQLAlchemy-реализация SiblingRepository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.sibling import SiblingRelation, SiblingType
from genealogy.domain.services.sibling_resolver import SiblingResolver
from genealogy.infrastructure.db.models.parent_child import ParentChild as ORMParentChild
from genealogy.infrastructure.relations.mapper import parent_child_to_domain


_SIBLING_TYPE_ORDER = {SiblingType.FULL: 0, SiblingType.HALF: 1, SiblingType.STEP: 2}


class SiblingRepositoryImpl:
    """
    SQLAlchemy-реализация SiblingRepository.

    Не хранит состояние между вызовами — каждый вызов = свежий запрос.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._resolver = SiblingResolver()

    async def get_siblings_of(self, person_id: str) -> list[SiblingRelation]:
        """2 запроса → список SiblingRelation, отсортированный FULL→HALF→STEP."""
        relations = await self._load_relations_for_persons([person_id])
        siblings = self._resolver.resolve(person_id, relations)
        return _sort_siblings(siblings)

    async def get_siblings_of_many(
        self,
        person_ids: list[str],
    ) -> dict[str, list[SiblingRelation]]:
        """
        Batch: 2 запроса для всех person_ids одновременно.
        Оптимальнее N вызовов get_siblings_of().
        """
        if not person_ids:
            return {}

        relations = await self._load_relations_for_persons(person_ids)

        result: dict[str, list[SiblingRelation]] = {}
        for pid in person_ids:
            siblings = self._resolver.resolve(pid, relations)
            result[pid] = _sort_siblings(siblings)

        return result

    async def _load_relations_for_persons(
        self,
        person_ids: list[str],
    ) -> list[ParentChildRelation]:
        """
        Загружает ParentChild-связи, достаточные для вычисления сиблингов.

        Шаг 1: найти parent_id для всех person_ids.
        Шаг 2: найти всех детей этих родителей.

        Возвращает объединение — все связи нужны SiblingResolver.
        """
        if not person_ids:
            return []

        stmt_parents = select(ORMParentChild).where(ORMParentChild.child_id.in_(person_ids))
        res: Result = await self._session.execute(stmt_parents)
        parent_links = [parent_child_to_domain(r) for r in res.scalars().all()]

        if not parent_links:
            return []

        parent_ids = list({r.parent_id for r in parent_links})

        stmt_siblings = select(ORMParentChild).where(ORMParentChild.parent_id.in_(parent_ids))
        res2: Result = await self._session.execute(stmt_siblings)
        sibling_links = [parent_child_to_domain(r) for r in res2.scalars().all()]

        # Объединяем, дедуплицируем по (parent_id, child_id)
        seen: set[tuple[str, str]] = set()
        all_relations: list[ParentChildRelation] = []

        for rel in parent_links + sibling_links:
            key = (rel.parent_id, rel.child_id)
            if key not in seen:
                seen.add(key)
                all_relations.append(rel)

        return all_relations


def _sort_siblings(siblings: list[SiblingRelation]) -> list[SiblingRelation]:
    """Сортировка: FULL → HALF → STEP, внутри группы по sibling_id."""
    return sorted(
        siblings,
        key=lambda s: (_SIBLING_TYPE_ORDER[s.sibling_type], s.sibling_id),
    )
