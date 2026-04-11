from typing import Any

from domain.entities.family import Family
from domain.entities.person import Person
from domain.exceptions import NotFoundValidationError
from domain.repositories.person import PersonFilters, PersonPage
from domain.value_objects.unset import UnsetType
from infrastructure.common.services import BaseService

from application.person.dto import PatchPersonCommand, PersonListQuery, PutPersonCommand


class PersonService(BaseService):
    async def get_person(self, person_id: str) -> Person:
        async with self.uow:
            person: Person = await self.repository_facade.person_repository.get_by_id(
                person_id=person_id,
            )

            return person

    async def get_persons_list(self, query: PersonListQuery) -> PersonPage:
        async with self.uow:
            filters = PersonFilters(
                family_id=query.family_id,
                gender=query.gender,
                first_name=query.first_name,
                last_name=query.last_name,
                sort=query.sort,
            )

            return await self.repository_facade.person_repository.get_list(
                filters=filters,
                limit=query.limit,
                offset=query.offset,
            )

    async def create_person(self, person: Person) -> Person:
        async with self.uow:
            await self._assert_family_exists(person.family_id)

            family = await self._load_family_aggregate(person.family_id)
            family.assert_can_add_member(person)

            created_person: Person = await self.repository_facade.person_repository.create(
                person=person,
            )

            return created_person

    async def update_person(self, command: PutPersonCommand) -> Person:
        async with self.uow:
            existing = await self.repository_facade.person_repository.get_by_id(
                person_id=command.person_id,
            )

            person: Person = self._apply_put_person(command=command, existing=existing)

            family = await self._load_family_aggregate(
                family_id=existing.family_id,
                exclude_person_id=existing.id,  # исключаем самого себя
            )
            family.assert_can_add_member(person)

            updated_person: Person = await self.repository_facade.person_repository.update(
                person=person,
            )

            return updated_person

    async def patch_update_person(self, command: PatchPersonCommand) -> Person:
        async with self.uow:
            existing = await self.repository_facade.person_repository.get_by_id(
                person_id=command.person_id,
            )

            updated_person: Person = self._apply_patch_update(
                command=command,
                existing=existing,
            )

            if self._patch_affects_identity(command):
                family = await self._load_family_aggregate(
                    family_id=existing.family_id,
                    exclude_person_id=existing.id,
                )
                family.assert_can_add_member(updated_person)

            return await self.repository_facade.person_repository.update(
                person=updated_person,
            )

    async def delete_person(self, person_id: str) -> None:
        async with self.uow:
            await self.repository_facade.person_repository.delete(
                person_id=person_id,
            )

            return None

    async def _assert_family_exists(self, family_id: str) -> None:
        """Проверка существования семьи — задача application-слоя."""
        exists = await self.repository_facade.family_repository.exists(family_id)
        if not exists:
            raise NotFoundValidationError(
                message="Семья не найдена",
                errors={"family_id": f"Семья с ID «{family_id}» не существует."},
            )

    async def _load_family_aggregate(
        self,
        family_id: str,
        exclude_person_id: str | None = None,
    ) -> Family:
        """
        Собирает агрегат Family с текущими членами.
        exclude_person_id — исключает конкретного человека из списка
        (нужно при update, чтобы не сравнивать запись саму с собой).
        """
        members = await self.repository_facade.person_repository.get_persons_by_family(
            family_id=family_id,
        )
        if exclude_person_id:
            members = [m for m in members if m.id != exclude_person_id]

        # Family.name здесь не важно для инвариантов — передаём заглушку.
        # Если нужно имя, добавьте get_family в FamilyRepository.
        return Family(id=family_id, name="", members=members)

    @staticmethod
    def _patch_affects_identity(command: PatchPersonCommand) -> bool:
        identity_fields = {"first_name", "last_name", "birth_date"}

        # Поля, которые реально переданы в команде (не UNSET)
        provided_fields = {
            field for field in command.__dataclass_fields__ if not isinstance(getattr(command, field), UnsetType)
        }

        return bool(identity_fields & provided_fields)

    def _apply_patch_update(self, command: PatchPersonCommand, existing: Person) -> Person:
        def resolve(command_value: object, existing_value: object) -> Any:
            if isinstance(command_value, UnsetType):
                return existing_value  # не трогаем
            return command_value  # берём из команды (даже если None)

        return Person(
            id=existing.id,
            family_id=existing.family_id,
            first_name=resolve(command.first_name, existing.first_name),
            last_name=resolve(command.last_name, existing.last_name),
            gender=resolve(command.gender, existing.gender),
            birth_date=resolve(command.birth_date, existing.birth_date),
            death_date=resolve(command.death_date, existing.death_date),
            birth_date_raw=resolve(command.birth_date_raw, existing.birth_date_raw),
            death_date_raw=resolve(command.death_date_raw, existing.death_date_raw),
        )

    def _apply_put_person(self, command: PutPersonCommand, existing: Person) -> Person:
        return Person(
            id=existing.id,
            family_id=existing.family_id,
            first_name=command.first_name,
            last_name=command.last_name,
            gender=command.gender,
            birth_date=command.birth_date,
            death_date=command.death_date,
            birth_date_raw=command.birth_date_raw,
            death_date_raw=command.death_date_raw,
        )
