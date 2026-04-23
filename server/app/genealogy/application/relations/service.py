"""
application/relations/service.py

Application service for Person relations (parent-child and spouse).

Rules:
- All reads AND writes for a single use-case happen inside ONE UoW context.
- Domain invariants are checked by dedicated policy services — not here.
- This service only orchestrates: load data → check policy → persist.
"""

from __future__ import annotations

from shared.domain.exceptions import NotFoundError, RelationDomainError

from genealogy.application.relations.commands import (
    AddParentChildCommand,
    AddSpouseCommand,
    DivorceCommand,
    EdgeDTO,
    FamilyGraphResult,
    NodeDTO,
)
from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.person import Person
from genealogy.domain.entities.spouse import SpouseRelation
from genealogy.domain.services.parent_child_policy import ParentChildPolicy
from genealogy.domain.services.spouse_policy import SpousePolicy
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory


class RelationService:
    def __init__(self, uow_factory: GenealogyUoWFactory) -> None:
        self._uow_factory = uow_factory
        self._parent_child_policy = ParentChildPolicy()
        self._spouse_policy = SpousePolicy()

    # ── ParentChild ───────────────────────────────────────────────────────────

    async def add_parent_child(self, command: AddParentChildCommand) -> ParentChildRelation:
        async with self._uow_factory.create(master=True) as uow:
            parent = await uow.persons.get_by_id(command.parent_id)
            child = await uow.persons.get_by_id(command.child_id)

            if parent.family_id != child.family_id:
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={"relation": "Нельзя связать персон из разных семей."},
                )

            existing_parent = await uow.parent_child.get_children_of(command.parent_id)
            existing_parent += await uow.parent_child.get_parents_of(command.child_id)

            existing_spouse = await uow.spouses.get_spouses_of(command.parent_id)
            existing_spouse += await uow.spouses.get_spouses_of(command.child_id)

            # Проверка через выделенный policy-сервис
            relation = self._parent_child_policy.assert_can_add(
                parent_id=command.parent_id,
                child_id=command.child_id,
                relation_type=command.relation_type,
                existing_parent_relations=existing_parent,
                existing_spouse_relations=existing_spouse,
            )

            return await uow.parent_child.save(relation)

    async def remove_parent_child(self, parent_id: str, child_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            if not await uow.parent_child.exists(parent_id, child_id):
                raise NotFoundError(resource="ParentChild relation", resource_id=parent_id)
            await uow.parent_child.remove(parent_id, child_id)

    # ── Spouse ────────────────────────────────────────────────────────────────

    async def add_spouse(self, command: AddSpouseCommand) -> SpouseRelation:
        async with self._uow_factory.create(master=True) as uow:
            # Убеждаемся что обе персоны существуют
            await uow.persons.get_by_id(command.person_a_id)
            await uow.persons.get_by_id(command.person_b_id)

            # Загружаем связи, необходимые для проверки инвариантов
            existing_spouse = await uow.spouses.get_spouses_of(command.person_a_id)
            existing_spouse += await uow.spouses.get_spouses_of(command.person_b_id)

            existing_parent = await uow.parent_child.get_children_of(command.person_a_id)
            existing_parent += await uow.parent_child.get_parents_of(command.person_b_id)
            existing_parent += await uow.parent_child.get_children_of(command.person_b_id)
            existing_parent += await uow.parent_child.get_parents_of(command.person_a_id)

            # Проверка через выделенный policy-сервис
            relation = self._spouse_policy.assert_can_add(
                person_a_id=command.person_a_id,
                person_b_id=command.person_b_id,
                existing_spouse_relations=existing_spouse,
                existing_parent_relations=existing_parent,
                marriage_status=command.marriage_status,
                marriage_year=command.marriage_year,
                marriage_month=command.marriage_month,
                marriage_day=command.marriage_day,
                marriage_place=command.marriage_place,
                marriage_date_raw=command.marriage_date_raw,
            )

            return await uow.spouses.save(relation)

    async def divorce(self, command: DivorceCommand) -> SpouseRelation:
        async with self._uow_factory.create(master=True) as uow:
            spouses = await uow.spouses.get_spouses_of(command.person_a_id)
            target = next((r for r in spouses if r.involves(command.person_b_id)), None)
            if target is None:
                raise NotFoundError(resource="Spouse relation", resource_id=command.person_a_id)

            updated = target.divorce(
                divorce_year=command.divorce_year,
                divorce_month=command.divorce_month,
                divorce_day=command.divorce_day,
                divorce_date_raw=command.divorce_date_raw,
            )
            return await uow.spouses.save(updated)

    async def remove_spouse(self, person_a_id: str, person_b_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            if not await uow.spouses.exists(person_a_id, person_b_id):
                raise NotFoundError(resource="Spouse relation", resource_id=person_a_id)
            await uow.spouses.remove(person_a_id, person_b_id)

    # ── Family graph ──────────────────────────────────────────────────────────

    async def get_family_graph(self, family_id: str) -> FamilyGraphResult:
        async with self._uow_factory.create(master=False) as uow:
            persons, parent_relations, spouse_relations = await uow.family_graph.get_persons_with_relations(family_id)

            # трансформация внутри контекста
            nodes = [_person_to_node(p) for p in persons]
            edges = [
                *[_parent_child_to_edge(r) for r in parent_relations],
                *[_spouse_to_edge(r) for r in spouse_relations],
            ]
            return FamilyGraphResult(nodes=nodes, edges=edges)


# ── Pure conversion helpers ───────────────────────────────────────────────────


def _person_to_node(person: Person) -> NodeDTO:
    return NodeDTO(
        id=person.id,
        full_name=person.full_name(),
        name=str(person.name),
        gender=person.gender.value,
        is_alive=person.is_alive(),
        birth_year=person.birth_date.year if person.birth_date else None,
        death_year=person.death_date.year if person.death_date else None,
        birth_date_raw=person.birth_date_raw,
    )


def _parent_child_to_edge(rel: ParentChildRelation) -> EdgeDTO:
    return EdgeDTO(
        type="parent_child",
        source_id=rel.parent_id,
        target_id=rel.child_id,
        relation_type=rel.relation_type.value,
    )


def _spouse_to_edge(rel: SpouseRelation) -> EdgeDTO:
    return EdgeDTO(
        type="spouse",
        source_id=rel.first_person_id,
        target_id=rel.second_person_id,
        marriage_status=rel.marriage_status.value,
        marriage_year=rel.marriage_year,
        divorce_year=rel.divorce_year,
    )
