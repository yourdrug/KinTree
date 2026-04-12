from typing import Any

from domain.entities.family import Family
from domain.exceptions import NotFoundValidationError
from domain.value_objects.unset import UnsetType
from infrastructure.common.services import BaseService

from application.family.dto import (
    PatchFamilyCommand,
    PutFamilyCommand,
)


class FamilyService(BaseService):
    async def get_family(self, family_id: str) -> Family:
        async with self.uow:
            family = await self.repository_facade.family_repository.get_by_id(
                family_id=family_id,
            )
            return family

    # async def get_families_list(self, query: FamilyListQuery):
    #     async with self.uow:
    #         return await self.repository_facade.family_repository.get_list(
    #             limit=query.limit,
    #             offset=query.offset,
    #         )

    async def create_family(self, family: Family) -> Family:
        async with self.uow:
            created = await self.repository_facade.family_repository.create(
                family=family,
            )
            return created

    async def update_family(self, command: PutFamilyCommand) -> Family:
        async with self.uow:
            existing = await self.repository_facade.family_repository.get_by_id(
                family_id=command.family_id,
            )

            updated = self._apply_put(command, existing)

            return await self.repository_facade.family_repository.update(
                family=updated,
            )

    async def patch_update_family(self, command: PatchFamilyCommand) -> Family:
        async with self.uow:
            existing = await self.repository_facade.family_repository.get_by_id(
                family_id=command.family_id,
            )

            updated = self._apply_patch(command, existing)

            return await self.repository_facade.family_repository.update(
                family=updated,
            )

    async def delete_family(self, family_id: str) -> None:
        async with self.uow:
            await self._assert_family_exists(family_id)

            await self.repository_facade.family_repository.delete(
                family_id=family_id,
            )

    async def get_family_with_members(self, family_id: str) -> Family:
        """
        Полезный метод: собрать агрегат Family с members
        (как ты делаешь в PersonService)
        """
        async with self.uow:
            family = await self.repository_facade.family_repository.get_by_id(
                family_id=family_id,
            )

            members = await self.repository_facade.person_repository.get_persons_by_family(
                family_id=family_id,
            )

            family.members = members
            return family

    async def _assert_family_exists(self, family_id: str) -> None:
        exists = await self.repository_facade.family_repository.exists(family_id)
        if not exists:
            raise NotFoundValidationError(
                message="Семья не найдена",
                errors={"family_id": f"Семья с ID «{family_id}» не существует."},
            )

    def _apply_put(self, command: PutFamilyCommand, existing: Family) -> Family:
        return Family(
            id=existing.id,
            name=command.name,
            owner_id=existing.owner_id,
            description=command.description,
            origin_place=command.origin_place,
            founded_year=command.founded_year,
            ended_year=command.ended_year,
            members=existing.members,  # агрегат сохраняем
        )

    def _apply_patch(self, command: PatchFamilyCommand, existing: Family) -> Family:
        def resolve(new: Any, old: Any) -> Any:
            if isinstance(new, UnsetType):
                return old
            return new

        return Family(
            id=existing.id,
            name=resolve(command.name, existing.name),
            owner_id=existing.owner_id,
            description=resolve(command.description, existing.description),
            origin_place=resolve(command.origin_place, existing.origin_place),
            founded_year=resolve(command.founded_year, existing.founded_year),
            ended_year=resolve(command.ended_year, existing.ended_year),
            members=existing.members,
        )
