from domain.entities.family import Family as DomainFamily
from domain.repositories.family import AbstractFamilyRepository
from sqlalchemy import Delete, Insert, Update, delete, exists, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.family import Family as ORMFamily
from infrastructure.family.family_mapper import FamilyORMMapper


class FamilyRepository(BaseRepository, AbstractFamilyRepository):
    async def exists(self, family_id: str) -> bool:
        """Проверяет существование семьи по ID."""
        statement: Select = select(exists().where(ORMFamily.id == family_id))
        result: Result = await self.session.execute(statement)
        return result.scalar() or False

    async def get_by_id(self, family_id: str) -> DomainFamily:
        statement: Select = select(ORMFamily).where(ORMFamily.id == family_id)
        result: Result = await self.session.execute(statement)
        person: ORMFamily = result.scalar_one()

        return FamilyORMMapper.to_domain(person)

    async def create(self, family: DomainFamily) -> DomainFamily:
        data = FamilyORMMapper.to_persistence(family)

        statement: Insert = insert(ORMFamily).values(**data).returning(ORMFamily)
        result: Result = await self.session.execute(statement)
        orm_family: ORMFamily = result.scalar_one()

        return FamilyORMMapper.to_domain(orm_family)

    async def update(self, family: DomainFamily) -> DomainFamily:
        data = FamilyORMMapper.to_persistence(family)

        statement: Update = update(ORMFamily).where(ORMFamily.id == family.id).values(**data).returning(ORMFamily)
        result: Result = await self.session.execute(statement)
        orm_family: ORMFamily = result.scalar_one()

        return FamilyORMMapper.to_domain(orm_family)

    async def delete(self, family_id: str) -> None:
        statement: Delete = delete(ORMFamily).where(ORMFamily.id == family_id)
        await self.session.execute(statement)

        return None
