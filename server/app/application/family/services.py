from typing import Any

from domain.entities.account import Account
from domain.entities.family import Family, create_family
from domain.exceptions import NotFoundError
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page
from domain.value_objects.unset import UnsetType

from application.family.commands import (
    CreateFamilyCommand,
    PatchFamilyCommand,
    PutFamilyCommand,
)
from application.uow_factory import UoWFactory


class FamilyService:
    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    async def get_family(self, family_id: str) -> Family:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.families.get_by_id(family_id=family_id)

    async def get_families_list(
        self,
        filters: BaseFilterSpec,
    ) -> Page[Family]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.families.list(
                spec=filters,
            )

    async def create_family(self, command: CreateFamilyCommand, account: Account) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            family: Family = create_family(
                name=command.name,
                owner_id=account.id,
                description=command.description,
                origin_place=command.origin_place,
                founded_year=command.founded_year,
                ended_year=command.ended_year,
            )

            created = await uow.families.save(family=family)
            return created

    async def update_family(self, command: PutFamilyCommand) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            existing: Family | None = await uow.families.get_by_id_or_none(
                family_id=command.family_id,
            )

            if not existing or existing.owner_id != command.owner_id:
                raise NotFoundError(resource="Family", resource_id=command.family_id)

            updated = self._apply_put(command, existing)

            return await uow.families.save(
                family=updated,
            )

    async def patch_update_family(self, command: PatchFamilyCommand) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            existing = await uow.families.get_by_id(
                family_id=command.family_id,
            )

            updated = self._apply_patch(command, existing)

            return await uow.families.save(
                family=updated,
            )

    async def delete_family(self, family_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            await uow.families.remove(
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
