"""
application/family/services.py

Application service for the Family aggregate.

Rules:
- Mutation is delegated to Family.apply_put() / Family.apply_patch().
- Services never build Family(...) directly for updates.
- Each use-case opens exactly one UoW context.
"""

from __future__ import annotations

from domain.entities.account import Account
from domain.entities.family import Family, create_family
from domain.exceptions import NotFoundError
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page
from infrastructure.uow_factory import UoWFactory

from application.family.commands import CreateFamilyCommand, PatchFamilyCommand, PutFamilyCommand


class FamilyService:
    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    # ── Queries ───────────────────────────────────────────────────────────────

    async def get_family(self, family_id: str) -> Family:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.families.get_by_id(family_id)

    async def get_families_list(self, spec: BaseFilterSpec) -> Page[Family]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.families.list(spec)

    # ── Commands ──────────────────────────────────────────────────────────────

    async def create_family(self, command: CreateFamilyCommand, account: Account) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            family = create_family(
                name=command.name,
                owner_id=account.id,
                description=command.description,
                origin_place=command.origin_place,
                founded_year=command.founded_year,
                ended_year=command.ended_year,
            )
            return await uow.families.save(family)

    async def update_family(self, command: PutFamilyCommand) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            family = await uow.families.get_by_id_or_none(command.family_id)

            if family is None:
                raise NotFoundError(resource="Family", resource_id=command.family_id)

            # Delegate full replacement to the entity — it validates its own invariants
            family.apply_put(
                name=command.name,
                description=command.description,
                origin_place=command.origin_place,
                founded_year=command.founded_year,
                ended_year=command.ended_year,
            )
            return await uow.families.save(family)

    async def patch_update_family(self, command: PatchFamilyCommand) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            family = await uow.families.get_by_id(command.family_id)

            # Delegate partial update to the entity
            family.apply_patch(
                name=command.name,
                description=command.description,
                origin_place=command.origin_place,
                founded_year=command.founded_year,
                ended_year=command.ended_year,
            )
            return await uow.families.save(family)

    async def delete_family(self, family_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            await uow.families.remove(family_id)
