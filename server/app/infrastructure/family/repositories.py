from domain.repositories.family import AbstractFamilyRepository
from sqlalchemy import exists, select
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.family import Family as ORMFamily


class FamilyRepository(BaseRepository, AbstractFamilyRepository):
    async def exists(self, family_id: str) -> bool:
        """Проверяет существование семьи по ID."""
        statement: Select = select(exists().where(ORMFamily.id == family_id))
        result: Result = await self.session.execute(statement)
        return result.scalar() or False
