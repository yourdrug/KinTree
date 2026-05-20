"""
application/person/service.py

"""

from __future__ import annotations

from shared.domain.value_objects.pagination import BaseFilterSpec, Page

from genealogy.application.person.commands import CreatePersonCommand, PatchPersonCommand, UpdatePersonCommand
from genealogy.application.uow import GenealogyUoW
from genealogy.domain.entities.person import Person, create_person
from genealogy.domain.value_objects.family_member_spec import FamilyMemberSpec
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory


class PersonService:
    def __init__(self, uow_factory: GenealogyUoWFactory) -> None:
        self._uow_factory = uow_factory

    async def get_person(self, person_id: str) -> Person:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.persons.get_by_id(person_id)

    async def list_persons(self, spec: BaseFilterSpec) -> Page[Person]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.persons.list(spec)

    async def create_person(self, command: CreatePersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            await uow.families.get_by_id(command.family_id)

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

            await self._check_family_duplicate(
                uow=uow,
                family_id=command.family_id,
                candidate=FamilyMemberSpec(
                    first_name=command.first_name,
                    last_name=command.last_name,
                    birth_date=command.birth_date,
                ),
                exclude_id=None,
            )

            return await uow.persons.save(person)

    async def update_person(self, command: UpdatePersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            person = await uow.persons.get_by_id(command.person_id)

            person.apply_put(
                gender=command.gender,
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            await self._check_family_duplicate(
                uow=uow,
                family_id=person.family_id,
                candidate=FamilyMemberSpec(
                    first_name=command.first_name,
                    last_name=command.last_name,
                    birth_date=command.birth_date,
                ),
                exclude_id=person.id,
            )

            return await uow.persons.save(person)

    async def patch_person(self, command: PatchPersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            person = await uow.persons.get_by_id(command.person_id)

            needs_duplicate_check = person.identity_fields_changed(
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
            )

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
                await self._check_family_duplicate(
                    uow=uow,
                    family_id=person.family_id,
                    candidate=FamilyMemberSpec(
                        first_name=person.first_name,
                        last_name=person.last_name,
                        birth_date=person.birth_date,
                    ),
                    exclude_id=person.id,
                )

            return await uow.persons.save(person)

    async def delete_person(self, person_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            await uow.persons.remove(person_id)

    @staticmethod
    async def _check_family_duplicate(
        uow: GenealogyUoW,
        family_id: str,
        candidate: FamilyMemberSpec,
        exclude_id: str | None,
    ) -> None:
        family = await uow.families.get_by_id(family_id)
        existing_persons = await uow.persons.find_by_family(family_id)

        specs = [
            FamilyMemberSpec(
                first_name=p.first_name,
                last_name=p.last_name,
                birth_date=p.birth_date,
            )
            for p in existing_persons
            if p.id != exclude_id
        ]

        family.load_member_specs(specs)
        family.assert_can_add_member(candidate)
