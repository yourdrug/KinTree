from domain.entities.family import Family as DomainFamily
from domain.exceptions import NotFoundError
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page
from sqlalchemy import Delete, delete, exists, func, insert, select, update
from sqlalchemy.engine.result import Result
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
        """Проверяет существование семьи по ID."""
        statement: Select = select(exists().where(ORMFamily.id == family_id))
        result: Result = await self._session.execute(statement)
        return result.scalar() or False

    async def get_by_id(self, family_id: str) -> DomainFamily:
        statement: Select = select(ORMFamily).where(ORMFamily.id == family_id)
        result: Result = await self._session.execute(statement)
        family: ORMFamily = result.scalar_one()

        if family is None:
            raise NotFoundError(resource="Family", resource_id=family_id)

        return self._mapper.to_domain(family)

    async def get_by_id_or_none(self, family_id: str) -> DomainFamily | None:
        statement: Select = select(ORMFamily).where(ORMFamily.id == family_id)
        result: Result = await self._session.execute(statement)
        family: ORMFamily | None = result.scalar()

        return self._mapper.to_domain(family) if family else None

    async def list(self, filters: BaseFilterSpec) -> Page[DomainFamily]:
        statement: Select = select(ORMFamily)

        statement = family_filter_translator.apply(statement, filters)
        total = await self._get_count(statement)
        statement = family_filter_translator.apply_pagination(statement, filters)

        result: Result = await self._session.execute(statement)
        persons = [self._mapper.to_domain(p) for p in result.scalars().all()]

        return Page(
            result=persons,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def save(self, family: DomainFamily) -> DomainFamily:
        """
        Upsert: INSERT если новый, UPDATE если существует.
        Определяем по exists() — избегаем ошибок при ON CONFLICT.
        """

        data = self._mapper.to_persistence(family)
        already_exists = await self.exists(family.id)

        if already_exists:
            statement = update(ORMFamily).where(ORMFamily.id == family.id).values(**data).returning(ORMFamily)
        else:
            statement = insert(ORMFamily).values(**data).returning(ORMFamily)

        result: Result = await self._session.execute(statement)
        orm_family: ORMFamily = result.scalar_one()

        return self._mapper.to_domain(orm_family)

    async def remove(self, family_id: str) -> None:
        statement: Delete = delete(ORMFamily).where(ORMFamily.id == family_id)
        await self._session.execute(statement)

        return None

    async def _get_count(self, filtered_stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
        result: Result = await self._session.execute(count_stmt)
        return result.scalar_one()
