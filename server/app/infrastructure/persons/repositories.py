from sqlalchemy import select, Insert, insert, Update, update, Delete, delete, Sequence
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select

from domain.models.person import Person
from infrastructure.common.repositories import BaseRepository


class PersonRepository(BaseRepository):
    async def get_person(self, person_id: str) -> Person:
        statement: Select = select(Person).where(Person.id == person_id)
        result: Result = await self.session.execute(statement)
        person: Person = result.scalar_one()

        return person

    async def get_persons_by_family(self, family_id: str) -> Sequence[Person]:
        statement: Select = select(Person).where(Person.family_id == family_id)
        result: Result = await self.session.execute(statement)
        family_persons: Sequence[Person] = result.scalars().all()

        return family_persons

    async def create_person(self, person_data: dict) -> str:
        statement: Insert = insert(Person).values(**person_data).returning(Person.id)
        result: Result = await self.session.execute(statement)
        person_id: str = result.scalar_one()

        return person_id

    async def update_person(self, person_id: str, person_data: dict) -> None:
        statement: Update = update(Person).where(Person.id == person_id).values(**person_data)
        await self.session.execute(statement)

        return None

    async def delete_person(self, person_id: str) -> None:
        statement: Delete = delete(Person).where(Person.id == person_id)
        await self.session.execute(statement)

        return None
