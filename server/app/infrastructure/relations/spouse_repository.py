from __future__ import annotations

from domain.entities.spouse import SpouseRelation
from sqlalchemy import and_, delete, exists, insert, or_, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.spouse import Spouse as ORMSpouse
from infrastructure.relations.mapper import (
    spouse_to_domain,
    spouse_to_persistence,
)


class SpouseRepositoryImpl:
    """
    SQLAlchemy-реализация SpouseRepository.

    Особенность:
    - пары хранятся в каноническом виде (sorted)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _canonical(self, a: str, b: str) -> tuple[str, str]:
        return (a, b) if a <= b else (b, a)

    async def get_spouses_of(self, person_id: str) -> list[SpouseRelation]:
        stmt = select(ORMSpouse).where(
            or_(
                ORMSpouse.first_person_id == person_id,
                ORMSpouse.second_person_id == person_id,
            )
        )
        result: Result = await self._session.execute(stmt)
        return [spouse_to_domain(r) for r in result.scalars().all()]

    async def exists(self, person_a_id: str, person_b_id: str) -> bool:
        first, second = self._canonical(person_a_id, person_b_id)

        stmt = select(
            exists().where(
                and_(
                    ORMSpouse.first_person_id == first,
                    ORMSpouse.second_person_id == second,
                )
            )
        )
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def save(self, relation: SpouseRelation) -> SpouseRelation:
        """
        Upsert:
        - если есть → update
        - иначе → insert
        """
        data = spouse_to_persistence(relation)
        first, second = self._canonical(relation.first_person_id, relation.second_person_id)

        already_exists = await self.exists(first, second)

        if already_exists:
            stmt = (
                update(ORMSpouse)
                .where(
                    and_(
                        ORMSpouse.first_person_id == first,
                        ORMSpouse.second_person_id == second,
                    )
                )
                .values(**data)
                .returning(ORMSpouse)
            )
        else:
            stmt = insert(ORMSpouse).values(**data).returning(ORMSpouse)

        result: Result = await self._session.execute(stmt)
        return spouse_to_domain(result.scalar_one())

    async def remove(self, person_a_id: str, person_b_id: str) -> None:
        first, second = self._canonical(person_a_id, person_b_id)

        stmt = delete(ORMSpouse).where(
            and_(
                ORMSpouse.first_person_id == first,
                ORMSpouse.second_person_id == second,
            )
        )
        await self._session.execute(stmt)
