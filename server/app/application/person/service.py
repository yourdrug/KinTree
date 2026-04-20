"""
application/person/service.py

Application service for the Person aggregate.

Rules:
- Never constructs PersonName or PartialDate directly — those are domain concerns.
- Mutation is delegated to Person.apply_put() / Person.apply_patch().
- Family-level duplicate check is delegated to Family.assert_can_add_member().
- Each use-case opens exactly one UoW context.
"""

from __future__ import annotations

from domain.entities.family import Family
from domain.entities.person import Person, create_person
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page

from application.person.commands import CreatePersonCommand, PatchPersonCommand, UpdatePersonCommand
from application.uow import UnitOfWork
from application.uow_factory import UoWFactory


class PersonService:
    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    # ── Queries ───────────────────────────────────────────────────────────────

    async def get_person(self, person_id: str) -> Person:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.persons.get_by_id(person_id)

    async def list_persons(self, spec: BaseFilterSpec) -> Page[Person]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.persons.list(spec)

    # ── Commands ──────────────────────────────────────────────────────────────

    async def create_person(self, command: CreatePersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            family = await self._load_family_with_members(uow, command.family_id)

            person = create_person(
                gender=command.gender,
                family_id=command.family_id,
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            # Domain invariant: family decides whether the member can be added
            family.assert_can_add_member(person)
            return await uow.persons.save(person)

    async def update_person(self, command: UpdatePersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            person = await uow.persons.get_by_id(command.person_id)

            # Delegate mutation to the entity — it owns its invariants
            person.apply_put(
                gender=command.gender,
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            # Check family-level duplicate invariant (exclude self)
            family = await self._load_family_with_members(uow, person.family_id, exclude_id=person.id)
            family.assert_can_add_member(person)

            return await uow.persons.save(person)

    async def patch_person(self, command: PatchPersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            person = await uow.persons.get_by_id(command.person_id)

            needs_duplicate_check = person.identity_fields_changed(
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
            )

            # Delegate mutation to the entity
            person.apply_patch(
                first_name=command.first_name,
                last_name=command.last_name,
                gender=command.gender,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            if needs_duplicate_check:
                family = await self._load_family_with_members(uow, person.family_id, exclude_id=person.id)
                family.assert_can_add_member(person)

            return await uow.persons.save(person)

    async def delete_person(self, person_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            await uow.persons.remove(person_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    async def _load_family_with_members(
        uow: UnitOfWork,
        family_id: str,
        exclude_id: str | None = None,
    ) -> Family:
        """
        Loads the Family aggregate populated with its current members.
        exclude_id: omit one person from the member list (used during update
        so the person isn't compared against itself).
        """
        family = await uow.families.get_by_id(family_id)
        members = await uow.persons.find_by_family(family_id)
        family.members = [m for m in members if m.id != exclude_id] if exclude_id else members
        return family
