"""
application/person/service.py

Application service for the Person aggregate.

Rules:
- Never constructs PersonName or PartialDate directly — those are domain concerns.
- Mutation is delegated to Person.apply_put() / Person.apply_patch().
- Family-level duplicate check uses FamilyMemberSpec — Family does not know about Person.
- Each use-case opens exactly one UoW context.
"""

from __future__ import annotations

from genealogy.application.uow import GenealogyUoW
from genealogy.domain.entities.person import Person, create_person
from genealogy.domain.value_objects.family_member_spec import FamilyMemberSpec
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory

from genealogy.application.person.commands import CreatePersonCommand, PatchPersonCommand, UpdatePersonCommand
from shared.domain.value_objects.pagination import BaseFilterSpec, Page


class PersonService:
    def __init__(self, uow_factory: GenealogyUoWFactory) -> None:
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
            # Строим кандидата
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

            # Проверяем инвариант дублирования через Family + FamilyMemberSpec
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

            # Делегируем мутацию сущности — она владеет своими инвариантами
            person.apply_put(
                gender=command.gender,
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            # Проверяем family-level инвариант, исключая саму персону
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

            # Делегируем мутацию сущности
            person.apply_patch(
                first_name=command.first_name,
                last_name=command.last_name,
                gender=command.gender,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            # Проверяем только если изменились identity-поля
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

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    async def _check_family_duplicate(
        uow: GenealogyUoW,
        family_id: str,
        candidate: FamilyMemberSpec,
        exclude_id: str | None,
    ) -> None:
        """
        Загружает Family, наполняет спецификациями существующих членов
        и проверяет инвариант дублирования.

        Family не знает о Person — получает только FamilyMemberSpec.
        exclude_id: исключить одну персону из проверки (используется при
        обновлении, чтобы персона не сравнивалась сама с собой).
        """
        family = await uow.families.get_by_id(family_id)
        existing_persons = await uow.persons.find_by_family(family_id)

        # Строим список спецификаций, исключая обновляемую персону
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
