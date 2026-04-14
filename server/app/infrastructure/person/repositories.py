from domain.entities.person import Person as DomainPerson
from domain.filters.base import BaseFilterSpec
from domain.repositories.person import AbstractPersonRepository, PersonPage
from sqlalchemy import Delete, Insert, Sequence, Update, delete, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.person import Person as ORMPerson
from infrastructure.person.filters import person_filter_translator
from infrastructure.person.person_mapper import PersonORMMapper


class PersonRepository(BaseRepository, AbstractPersonRepository):
    async def exists(self, object_id: str) -> bool:
        return await self._check_exists(object_id=object_id, model=ORMPerson)

    async def get_by_id(self, person_id: str) -> DomainPerson:
        statement: Select = select(ORMPerson).where(ORMPerson.id == person_id)
        result: Result = await self.session.execute(statement)
        person: ORMPerson = result.scalar_one()

        return PersonORMMapper.to_domain(person)

    async def get_list(
        self,
        filters: BaseFilterSpec,
    ) -> PersonPage:
        statement: Select = select(ORMPerson)

        statement = person_filter_translator.apply(statement, filters)
        total = await self._get_count(statement)
        statement = person_filter_translator.apply_pagination(statement, filters)

        result: Result = await self.session.execute(statement)
        persons = [PersonORMMapper.to_domain(p) for p in result.scalars().all()]

        return PersonPage(
            result=persons,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def get_persons_by_family(self, family_id: str) -> list[DomainPerson]:
        """Возвращает всех членов семьи (для проверки инвариантов агрегата)."""
        statement: Select = select(ORMPerson).where(ORMPerson.family_id == family_id)
        result: Result = await self.session.execute(statement)
        orm_persons: Sequence[ORMPerson] = result.scalars().all()

        return [PersonORMMapper.to_domain(person) for person in orm_persons]

    async def create(self, person: DomainPerson) -> DomainPerson:
        data = PersonORMMapper.to_persistence(person)

        statement: Insert = insert(ORMPerson).values(**data).returning(ORMPerson)
        result: Result = await self.session.execute(statement)
        orm_person: ORMPerson = result.scalar_one()

        return PersonORMMapper.to_domain(orm_person)

    async def update(self, person: DomainPerson) -> DomainPerson:
        data = PersonORMMapper.to_persistence(person)

        statement: Update = update(ORMPerson).where(ORMPerson.id == person.id).values(**data).returning(ORMPerson)
        result: Result = await self.session.execute(statement)
        orm_person: ORMPerson = result.scalar_one()

        return PersonORMMapper.to_domain(orm_person)

    async def delete(self, person_id: str) -> None:
        statement: Delete = delete(ORMPerson).where(ORMPerson.id == person_id)
        await self.session.execute(statement)

        return None
