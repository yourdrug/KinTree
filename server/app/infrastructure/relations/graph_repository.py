from __future__ import annotations

from domain.entities.parent_child import ParentChildRelation
from domain.entities.person import Person
from domain.entities.spouse import SpouseRelation
from sqlalchemy import or_, select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.parent_child import ParentChild as ORMParentChild
from infrastructure.db.models.person import Person as ORMPerson
from infrastructure.db.models.spouse import Spouse as ORMSpouse
from infrastructure.person.mapper import PersonMapper
from infrastructure.relations.mapper import parent_child_to_domain, spouse_to_domain


class FamilyGraphRepositoryImpl:
    """
    Отвечает исключительно за построение графа семьи.
    Единственное место в проекте, где ParentChild/Spouse репозитории
    делают JOIN с таблицей Person — это его законная ответственность.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_persons_with_relations(
        self,
        family_id: str,
    ) -> tuple[list[Person], list[ParentChildRelation], list[SpouseRelation]]:
        persons = await self._fetch_persons(family_id)
        if not persons:
            return [], [], []

        person_ids = [p.id for p in persons]
        parent_relations = await self._fetch_parent_child(person_ids)
        spouse_relations = await self._fetch_spouses(person_ids)

        return persons, parent_relations, spouse_relations

    async def _fetch_persons(self, family_id: str) -> list[Person]:
        result: Result = await self._session.execute(select(ORMPerson).where(ORMPerson.family_id == family_id))
        return [PersonMapper.to_domain(row) for row in result.scalars().all()]

    async def _fetch_parent_child(self, person_ids: list[str]) -> list[ParentChildRelation]:
        if not person_ids:
            return []
        result: Result = await self._session.execute(
            select(ORMParentChild).where(
                or_(
                    ORMParentChild.parent_id.in_(person_ids),
                    ORMParentChild.child_id.in_(person_ids),
                )
            )
        )
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def _fetch_spouses(self, person_ids: list[str]) -> list[SpouseRelation]:
        if not person_ids:
            return []
        result: Result = await self._session.execute(
            select(ORMSpouse).where(
                or_(
                    ORMSpouse.first_person_id.in_(person_ids),
                    ORMSpouse.second_person_id.in_(person_ids),
                )
            )
        )
        return [spouse_to_domain(r) for r in result.scalars().all()]
