"""
infrastructure/person/repositories.py
"""

from __future__ import annotations

from shared.domain.exceptions import NotFoundError
from shared.domain.value_objects.pagination import BaseFilterSpec
from shared.infrastructure.db.filters.translator import FilterTranslator
from sqlalchemy import delete, exists, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from genealogy.domain.entities.person import Person
from genealogy.domain.repositories.person import Page
from genealogy.infrastructure.db.models.person import Person as ORMPerson
from genealogy.infrastructure.person.filters import person_filter_translator
from genealogy.infrastructure.person.mapper import PersonMapper


class PersonRepositoryImpl:
    """
    SQLAlchemy-реализация репозитория Person.

    Следует Protocol PersonRepository — явное наследование не нужно.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._translator: FilterTranslator = person_filter_translator

    async def get_by_id(self, person_id: str) -> Person:
        stmt = select(ORMPerson).where(ORMPerson.id == person_id)
        result: Result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            raise NotFoundError(resource="Person", resource_id=person_id)
        return PersonMapper.to_domain(orm)

    async def find_by_family(self, family_id: str) -> list[Person]:
        stmt = select(ORMPerson).where(ORMPerson.family_id == family_id)
        result: Result = await self._session.execute(stmt)
        return [PersonMapper.to_domain(row) for row in result.scalars().all()]

    async def list(self, spec: BaseFilterSpec) -> Page[Person]:
        stmt: Select = select(ORMPerson)
        stmt = self._translator.apply(stmt, spec)
        total = await self._get_count(stmt)
        stmt = self._translator.apply_pagination(stmt, spec)

        result: Result = await self._session.execute(stmt)
        persons = [PersonMapper.to_domain(row) for row in result.scalars().all()]

        return Page(result=persons, total=total, limit=spec.limit, offset=spec.offset)

    async def save(self, person: Person) -> Person:
        """Атомарный UPSERT через PostgreSQL INSERT ... ON CONFLICT DO UPDATE."""
        data = PersonMapper.to_persistence(person)
        update_data = {k: v for k, v in data.items() if k != "id"}

        stmt = (
            pg_insert(ORMPerson)
            .values(**data)
            .on_conflict_do_update(
                index_elements=["id"],
                set_=update_data,
            )
            .returning(ORMPerson)
        )
        result: Result = await self._session.execute(stmt)
        orm = result.scalar_one()
        return PersonMapper.to_domain(orm)

    async def remove(self, person_id: str) -> None:
        stmt = delete(ORMPerson).where(ORMPerson.id == person_id)
        await self._session.execute(stmt)

    async def exists(self, person_id: str) -> bool:
        stmt = select(exists().where(ORMPerson.id == person_id))
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def _get_count(self, filtered_stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
        result: Result = await self._session.execute(count_stmt)
        return result.scalar_one()
