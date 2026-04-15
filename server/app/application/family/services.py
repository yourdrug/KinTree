from typing import Any

from domain.entities.account import Account
from domain.entities.family import Family, create_family
from domain.exceptions import NotFoundValidationError
from domain.filters.base import BaseFilterSpec
from domain.filters.page import FamilyPage
from domain.value_objects.unset import UnsetType
from infrastructure.common.services import BaseService

from application.family.dto import (
    CreateFamilyCommand,
    PatchFamilyCommand,
    PutFamilyCommand,
)


class FamilyService(BaseService):
    # TODO ref get_by_id_or_None

    async def get_family(self, family_id: str) -> Family:
        async with self.uow:
            family = await self.repository_facade.family_repository.get_by_id(
                family_id=family_id,
            )
            return family

    async def get_families_list(
        self,
        filters: BaseFilterSpec,
    ) -> FamilyPage:
        async with self.uow:
            return await self.repository_facade.family_repository.get_list(
                filters=filters,
            )

    async def create_family(self, command: CreateFamilyCommand, account: Account) -> Family:
        async with self.uow:
            family: Family = create_family(
                name=command.name,
                owner_id=account.id,
                description=command.description,
                origin_place=command.origin_place,
                founded_year=command.founded_year,
                ended_year=command.ended_year,
            )

            created = await self.repository_facade.family_repository.create(
                family=family,
            )
            return created

    async def update_family(self, command: PutFamilyCommand) -> Family:
        async with self.uow:
            existing: Family | None = await self.repository_facade.family_repository.get_by_id_or_none(
                family_id=command.family_id,
            )

            if not existing or existing.owner_id != command.owner_id:
                raise NotFoundValidationError(
                    message="Ошибка валидации",
                    errors={"family_id": "Объект не существует."},
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
            await self.repository_facade.family_repository.delete(
                family_id=family_id,
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
            members=existing.members,
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
