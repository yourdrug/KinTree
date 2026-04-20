from __future__ import annotations

from domain.entities.parent_child import ParentChildRelation
from domain.entities.person import Person
from domain.entities.spouse import SpouseRelation
from domain.exceptions import NotFoundError
from domain.services.relation_policy import RelationPolicy

from application.relations.commands import (
    AddParentChildCommand,
    AddSpouseCommand,
    DivorceCommand,
    EdgeDTO,
    FamilyGraphResult,
    NodeDTO,
)
from application.uow_factory import UoWFactory


class RelationService:
    """
    Application-сервис управления связями.
    Логика проверок делегируется RelationPolicy.
    Построение графа — отдельный метод.
    """

    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory
        self._policy = RelationPolicy()

    # ── ParentChild ──────────────────────────────────────────────────────────

    async def add_parent_child(self, command: AddParentChildCommand) -> ParentChildRelation:
        async with self._uow_factory.create(master=False) as uow:
            # Проверяем что обе персоны существуют
            await uow.persons.get_by_id(command.parent_id)
            await uow.persons.get_by_id(command.child_id)

        # Загружаем существующие связи для проверки инвариантов
        existing_parent = await uow.parent_child.get_children_of(command.parent_id)
        existing_parent += await uow.parent_child.get_parents_of(command.child_id)

        existing_spouse = await uow.spouses.get_spouses_of(command.parent_id)
        existing_spouse += await uow.spouses.get_spouses_of(command.child_id)

        # Доменный сервис проверяет инварианты и создаёт объект
        relation = self._policy.assert_can_add_parent_child(
            parent_id=command.parent_id,
            child_id=command.child_id,
            relation_type=command.relation_type,
            existing_parent_relations=existing_parent,
            existing_spouse_relations=existing_spouse,
        )

        async with self._uow_factory.create(master=True) as uow:
            return await uow.parent_child.save(relation)

    async def remove_parent_child(self, parent_id: str, child_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            exists = await uow.parent_child.exists(parent_id, child_id)
            if not exists:
                raise NotFoundError(
                    resource="Relation",
                    resource_id=parent_id,
                )
            await uow.parent_child.remove(parent_id, child_id)

    # ── Spouse ───────────────────────────────────────────────────────────────

    async def add_spouse(self, command: AddSpouseCommand) -> SpouseRelation:
        async with self._uow_factory.create(master=True) as uow:
            await uow.persons.get_by_id(command.person_a_id)
            await uow.persons.get_by_id(command.person_b_id)

            existing_spouse = await uow.spouses.get_spouses_of(command.person_a_id)
            existing_spouse += await uow.spouses.get_spouses_of(command.person_b_id)

            existing_parent = await uow.parent_child.get_children_of(command.person_a_id)
            existing_parent += await uow.parent_child.get_parents_of(command.person_b_id)
            existing_parent += await uow.parent_child.get_children_of(command.person_b_id)
            existing_parent += await uow.parent_child.get_parents_of(command.person_a_id)

            relation = self._policy.assert_can_add_spouse(
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
            target = next(
                (r for r in spouses if r.involves(command.person_b_id)),
                None,
            )
            if target is None:
                raise NotFoundError(
                    resource="Spouse",
                    resource_id=command.person_a_id,
                )

            updated = target.divorce(
                divorce_year=command.divorce_year,
                divorce_month=command.divorce_month,
                divorce_day=command.divorce_day,
                divorce_date_raw=command.divorce_date_raw,
            )
            return await uow.spouses.save(updated)

    async def remove_spouse(self, person_a_id: str, person_b_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            exists = await uow.spouses.exists(person_a_id, person_b_id)
            if not exists:
                raise NotFoundError(
                    resource="Spouse",
                    resource_id=person_a_id,
                )
            await uow.spouses.remove(person_a_id, person_b_id)

    # ── Family Graph ──────────────────────────────────────────────────────────

    async def get_family_graph(self, family_id: str) -> FamilyGraphResult:
        """
        Возвращает граф семьи: узлы (персоны) + рёбра (связи).
        Один запрос на персон, один на parent_child, один на spouses.
        Итого: 3 запроса на всю семью.
        """
        async with self._uow_factory.create(master=False) as uow:
            persons = await uow.persons.find_by_family(family_id)

            if not persons:
                return FamilyGraphResult(nodes=[], edges=[])

            person_ids = [p.id for p in persons]

            # Один запрос для всех связей
            parent_relations = await uow.parent_child.get_all_for_persons(person_ids)
            spouse_relations = await uow.spouses.get_all_for_persons(person_ids)

            nodes = [_person_to_node(p) for p in persons]
            edges = [
                *[_parent_child_to_edge(r) for r in parent_relations],
                *[_spouse_to_edge(r) for r in spouse_relations],
            ]

            return FamilyGraphResult(nodes=nodes, edges=edges)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _person_to_node(person: Person) -> NodeDTO:
    return NodeDTO(
        id=person.id,
        name=str(person.name),
        full_name=person.full_name(),
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
