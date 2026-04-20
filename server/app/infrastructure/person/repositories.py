"""
infrastructure/person/repositories.py

Реализация репозитория Person через SQLAlchemy.

Принципы:
- Реализует Protocol PersonRepository — структурное соответствие.
- Знает о ORM-моделях и маппере, не знает о доменной логике.
- save() = upsert: если id существует — UPDATE, иначе INSERT.
- get_by_id() бросает NotFoundError (доменное исключение), не sqlalchemy.exc.
- Пагинация и фильтрация делегируются FilterTranslator.
"""

from __future__ import annotations

from domain.entities.person import Person
from domain.exceptions import NotFoundError
from domain.filters.base import BaseFilterSpec
from domain.repositories.person import Page
from sqlalchemy import delete, exists, func, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from infrastructure.db.filters.translator import FilterTranslator
from infrastructure.db.models.person import Person as ORMPerson
from infrastructure.person.filters import person_filter_translator
from infrastructure.person.mapper import PersonMapper


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
        """
        Upsert: INSERT если новый, UPDATE если существует.
        Определяем по exists() — избегаем ошибок при ON CONFLICT.
        """
        data = PersonMapper.to_persistence(person)
        already_exists = await self.exists(person.id)

        if already_exists:
            stmt = update(ORMPerson).where(ORMPerson.id == person.id).values(**data).returning(ORMPerson)
        else:
            stmt = insert(ORMPerson).values(**data).returning(ORMPerson)

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
