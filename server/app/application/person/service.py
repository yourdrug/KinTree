from domain.entities.person import Person
from infrastructure.common.services import BaseService

from application.person.dto import PatchPersonCommand, PutPersonCommand


class PersonService(BaseService):
    async def get_person(self, person_id: str) -> Person:
        async with self.uow:
            person: Person = await self.repository_facade.person_repository.get_person(
                person_id=person_id,
            )

            return person

    async def create_person(self, person: Person) -> Person:
        async with self.uow:
            created_person: Person = await self.repository_facade.person_repository.create_person(
                person=person,
            )

            return created_person

    async def update_person(self, command: PutPersonCommand) -> Person:
        async with self.uow:
            existing = await self.repository_facade.person_repository.get_person(
                person_id=command.person_id,
            )

            person: Person = await self._apply_put_person(command=command, existing=existing)

            updated_person: Person = await self.repository_facade.person_repository.update_person(
                person=person,
            )

            return updated_person

    async def patch_update_person(self, command: PatchPersonCommand) -> Person:
        async with self.uow:
            existing = await self.repository_facade.person_repository.get_person(
                person_id=command.person_id,
            )

            updated_person: Person = await self._apply_patch_update(
                command=command,
                existing=existing,
            )

            return await self.repository_facade.person_repository.update_person(
                person=updated_person,
            )

    async def delete_person(self, person_id: str) -> None:
        async with self.uow:
            await self.repository_facade.person_repository.delete_person(
                person_id=person_id,
            )

            return None

    async def _apply_patch_update(self, command: PatchPersonCommand, existing: Person) -> Person:
        data = existing.__dict__.copy()

        for field in command.update_fields:
            if field == "person_id":
                continue

            data[field] = getattr(command, field)

        data["id"] = command.person_id

        return Person(**data)

    async def _apply_put_person(self, command: PutPersonCommand, existing: Person) -> Person:
        return Person(
            id=existing.id,
            first_name=command.first_name,
            last_name=command.last_name,
            gender=command.gender,
            family_id=existing.family_id,
            birth_date=command.birth_date,
            death_date=command.death_date,
            birth_date_raw=command.birth_date_raw,
            death_date_raw=command.death_date_raw,
        )
