from __future__ import annotations

from sqlalchemy import and_, delete, exists, insert, select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.infrastructure.db.models.parent_child import ParentChild as ORMParentChild
from genealogy.infrastructure.relations.mapper import (
    parent_child_to_domain,
    parent_child_to_persistence,
)


class ParentChildRepositoryImpl:
    """
    SQLAlchemy-реализация ParentChildRepository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_parents_of(self, person_id: str) -> list[ParentChildRelation]:
        stmt = select(ORMParentChild).where(ORMParentChild.child_id == person_id)
        result: Result = await self._session.execute(stmt)
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def get_children_of(self, person_id: str) -> list[ParentChildRelation]:
        stmt = select(ORMParentChild).where(ORMParentChild.parent_id == person_id)
        result: Result = await self._session.execute(stmt)
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def exists(self, parent_id: str, child_id: str) -> bool:
        stmt = select(
            exists().where(
                and_(
                    ORMParentChild.parent_id == parent_id,
                    ORMParentChild.child_id == child_id,
                )
            )
        )
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def save(self, relation: ParentChildRelation) -> ParentChildRelation:
        """
        CREATE ONLY (дубликаты контролируются доменом).
        """
        data = parent_child_to_persistence(relation)

        stmt = insert(ORMParentChild).values(**data).returning(ORMParentChild)
        result: Result = await self._session.execute(stmt)

        return parent_child_to_domain(result.scalar_one())

    async def remove(self, parent_id: str, child_id: str) -> None:
        stmt = delete(ORMParentChild).where(
            and_(
                ORMParentChild.parent_id == parent_id,
                ORMParentChild.child_id == child_id,
            )
        )
        await self._session.execute(stmt)
