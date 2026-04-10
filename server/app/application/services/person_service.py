from domain.models.person import Person

from infrastructure.common.services import BaseService


class PersonService(BaseService):
    async def get_person(self, person_id: str) -> Person:
        async with self.uow:
            person: Person = await self.repository_facade.person_repository.get_person(
                person_id=person_id,
            )

            return person

    async def create_person(self, person_data: dict) -> str:
        async with self.uow:
            person_id: str = await self.repository_facade.person_repository.create_person(
                person_data=person_data,
            )

            return person_id

    async def update_person(self, person_id: str, person_data: dict) -> Person:
        async with self.uow:
            await self.repository_facade.person_repository.update_person(
                person_id=person_id,
                person_data=person_data,
            )

            person: Person = await self.repository_facade.person_repository.get_person(
                person_id=person_id,
            )

            return person

    async def delete_person(self, person_id: str) -> None:
        async with self.uow:
            await self.repository_facade.person_repository.delete_person(
                person_id=person_id,
            )

            return None
