from domain.entities.person import Person as DomainPerson
from sqlalchemy import Delete, Insert, Update, delete, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.person import Person as ORMPerson
from infrastructure.person.person_mapper import PersonORMMapper


class PersonRepository(BaseRepository):
    async def get_person(self, person_id: str) -> DomainPerson:
        statement: Select = select(ORMPerson).where(ORMPerson.id == person_id)
        result: Result = await self.session.execute(statement)
        person: ORMPerson = result.scalar_one()

        return PersonORMMapper.to_domain(person)

    # async def get_persons_by_family(self, family_id: str) -> Sequence[DomainPerson]:
    #     statement: Select = select(ORMPerson).where(ORMPerson.family_id == family_id)
    #     result: Result = await self.session.execute(statement)
    #     family_persons: Sequence[ORMPerson] = result.scalars().all()
    #
    #     return family_persons

    async def create_person(self, person: DomainPerson) -> DomainPerson:
        data = PersonORMMapper.to_persistence(person)

        statement: Insert = insert(ORMPerson).values(**data).returning(ORMPerson.id)
        result: Result = await self.session.execute(statement)
        person_id: str = result.scalar_one()

        return await self.get_person(person_id)

    async def update_person(self, person: DomainPerson) -> DomainPerson:
        data = PersonORMMapper.to_persistence(person)

        statement: Update = update(ORMPerson).where(ORMPerson.id == person.id).values(**data).returning(ORMPerson)
        result: Result = await self.session.execute(statement)
        orm_person: ORMPerson = result.scalar_one()

        return PersonORMMapper.to_domain(orm_person)

    async def delete_person(self, person_id: str) -> None:
        statement: Delete = delete(ORMPerson).where(ORMPerson.id == person_id)
        await self.session.execute(statement)

        return None
