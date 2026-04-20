"""
infrastructure/family/repositories.py

SQLAlchemy implementation of FamilyRepository.

Rules:
- No domain validation here — only data access.
- get_by_id raises NotFoundError (domain exception); repository translates
  ORM-level NoResultFound into it.
- save() is an upsert (INSERT or UPDATE based on existence check).
"""

from __future__ import annotations

from domain.entities.family import Family as DomainFamily
from domain.exceptions import NotFoundError
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page
from sqlalchemy import Delete, delete, exists, func, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from infrastructure.db.filters.translator import FilterTranslator
from infrastructure.db.models.family import Family as ORMFamily
from infrastructure.family.filters import family_filter_translator
from infrastructure.family.mapper import FamilyMapper


class FamilyRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._translator: FilterTranslator = family_filter_translator
        self._mapper = FamilyMapper()

    async def exists(self, family_id: str) -> bool:
        stmt = select(exists().where(ORMFamily.id == family_id))
        result: Result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def get_by_id(self, family_id: str) -> DomainFamily:
        stmt = select(ORMFamily).where(ORMFamily.id == family_id)
        result: Result = await self._session.execute(stmt)
        try:
            orm_family = result.scalar_one()
        except NoResultFound as exception:
            raise NotFoundError(resource="Family", resource_id=family_id) from exception
        return self._mapper.to_domain(orm_family)

    async def get_by_id_or_none(self, family_id: str) -> DomainFamily | None:
        stmt = select(ORMFamily).where(ORMFamily.id == family_id)
        result: Result = await self._session.execute(stmt)
        orm_family = result.scalar_one_or_none()
        return self._mapper.to_domain(orm_family) if orm_family else None

    async def list(self, spec: BaseFilterSpec) -> Page[DomainFamily]:
        stmt: Select = select(ORMFamily)
        stmt = self._translator.apply(stmt, spec)
        total = await self._count(stmt)
        stmt = self._translator.apply_pagination(stmt, spec)
        result: Result = await self._session.execute(stmt)
        families = [self._mapper.to_domain(row) for row in result.scalars().all()]
        return Page(result=families, total=total, limit=spec.limit, offset=spec.offset)

    async def save(self, family: DomainFamily) -> DomainFamily:
        data = self._mapper.to_persistence(family)
        already_exists = await self.exists(family.id)
        if already_exists:
            stmt = update(ORMFamily).where(ORMFamily.id == family.id).values(**data).returning(ORMFamily)
        else:
            stmt = insert(ORMFamily).values(**data).returning(ORMFamily)
        result: Result = await self._session.execute(stmt)
        return self._mapper.to_domain(result.scalar_one())

    async def remove(self, family_id: str) -> None:
        stmt: Delete = delete(ORMFamily).where(ORMFamily.id == family_id)
        await self._session.execute(stmt)

    async def _count(self, filtered_stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
        result: Result = await self._session.execute(count_stmt)
        return result.scalar_one()
