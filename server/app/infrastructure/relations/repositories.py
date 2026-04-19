from __future__ import annotations

from domain.entities.parent_child import ParentChildRelation
from domain.entities.spouse import SpouseRelation
from domain.exceptions import NotFoundValidationError
from domain.repositories.relations import AbstractParentChildRepository, AbstractSpouseRepository
from sqlalchemy import and_, delete, insert, or_, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.exc import NoResultFound

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.parent_child import ParentChild as ORMParentChild
from infrastructure.db.models.spouse import Spouse as ORMSpouse
from infrastructure.relations.mapper import (
    parent_child_to_domain,
    parent_child_to_persistence,
    spouse_to_domain,
    spouse_to_persistence,
)


class ParentChildRepository(BaseRepository, AbstractParentChildRepository):
    async def get_by_family(self, family_id: str) -> list[ParentChildRelation]:
        """
        Все родительские связи в семье.
        Делаем JOIN с Person чтобы фильтровать по family_id.
        """
        from infrastructure.db.models.person import Person as ORMPerson

        stmt = (
            select(ORMParentChild)
            .join(ORMPerson, ORMPerson.id == ORMParentChild.parent_id)
            .where(ORMPerson.family_id == family_id)
        )
        result: Result = await self.session.execute(stmt)
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def get_parents_of(self, person_id: str) -> list[ParentChildRelation]:
        stmt = select(ORMParentChild).where(ORMParentChild.child_id == person_id)
        result: Result = await self.session.execute(stmt)
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def get_children_of(self, person_id: str) -> list[ParentChildRelation]:
        stmt = select(ORMParentChild).where(ORMParentChild.parent_id == person_id)
        result: Result = await self.session.execute(stmt)
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def get_all_for_persons(self, person_ids: list[str]) -> list[ParentChildRelation]:
        """Один запрос для всех связей — используется при построении графа."""
        if not person_ids:
            return []
        stmt = select(ORMParentChild).where(
            or_(
                ORMParentChild.parent_id.in_(person_ids),
                ORMParentChild.child_id.in_(person_ids),
            )
        )
        result: Result = await self.session.execute(stmt)
        return [parent_child_to_domain(r) for r in result.scalars().all()]

    async def exists(self, parent_id: str, child_id: str) -> bool:
        stmt = select(ORMParentChild).where(
            and_(
                ORMParentChild.parent_id == parent_id,
                ORMParentChild.child_id == child_id,
            )
        )
        result: Result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, relation: ParentChildRelation) -> ParentChildRelation:
        data = parent_child_to_persistence(relation)
        stmt = insert(ORMParentChild).values(**data).returning(ORMParentChild)
        result: Result = await self.session.execute(stmt)
        return parent_child_to_domain(result.scalar_one())

    async def delete(self, parent_id: str, child_id: str) -> None:
        stmt = delete(ORMParentChild).where(
            and_(
                ORMParentChild.parent_id == parent_id,
                ORMParentChild.child_id == child_id,
            )
        )
        await self.session.execute(stmt)


class SpouseRepository(BaseRepository, AbstractSpouseRepository):
    def _canonical(self, a: str, b: str) -> tuple[str, str]:
        """Приводим пару к канонической форме для запросов."""
        first, second = sorted([a, b])
        return first, second

    async def get_by_family(self, family_id: str) -> list[SpouseRelation]:
        from infrastructure.db.models.person import Person as ORMPerson

        stmt = (
            select(ORMSpouse)
            .join(ORMPerson, ORMPerson.id == ORMSpouse.first_person_id)
            .where(ORMPerson.family_id == family_id)
        )
        result: Result = await self.session.execute(stmt)
        return [spouse_to_domain(r) for r in result.scalars().all()]

    async def get_spouses_of(self, person_id: str) -> list[SpouseRelation]:
        stmt = select(ORMSpouse).where(
            or_(
                ORMSpouse.first_person_id == person_id,
                ORMSpouse.second_person_id == person_id,
            )
        )
        result: Result = await self.session.execute(stmt)
        return [spouse_to_domain(r) for r in result.scalars().all()]

    async def get_all_for_persons(self, person_ids: list[str]) -> list[SpouseRelation]:
        if not person_ids:
            return []
        stmt = select(ORMSpouse).where(
            or_(
                ORMSpouse.first_person_id.in_(person_ids),
                ORMSpouse.second_person_id.in_(person_ids),
            )
        )
        result: Result = await self.session.execute(stmt)
        return [spouse_to_domain(r) for r in result.scalars().all()]

    async def exists(self, person_a_id: str, person_b_id: str) -> bool:
        first, second = self._canonical(person_a_id, person_b_id)
        stmt = select(ORMSpouse).where(
            and_(
                ORMSpouse.first_person_id == first,
                ORMSpouse.second_person_id == second,
            )
        )
        result: Result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, relation: SpouseRelation) -> SpouseRelation:
        data = spouse_to_persistence(relation)
        stmt = insert(ORMSpouse).values(**data).returning(ORMSpouse)
        result: Result = await self.session.execute(stmt)
        return spouse_to_domain(result.scalar_one())

    async def update(self, relation: SpouseRelation) -> SpouseRelation:
        data = spouse_to_persistence(relation)
        first, second = self._canonical(relation.first_person_id, relation.second_person_id)
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
        result: Result = await self.session.execute(stmt)
        try:
            return spouse_to_domain(result.scalar_one())
        except NoResultFound as exc:
            raise NotFoundValidationError(
                message="Связь не найдена",
                errors={"spouse": "Запись о браке не найдена."},
            ) from exc

    async def delete(self, person_a_id: str, person_b_id: str) -> None:
        first, second = self._canonical(person_a_id, person_b_id)
        stmt = delete(ORMSpouse).where(
            and_(
                ORMSpouse.first_person_id == first,
                ORMSpouse.second_person_id == second,
            )
        )
        await self.session.execute(stmt)
