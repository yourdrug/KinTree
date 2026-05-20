"""
genealogy/domain/services/spouse_policy.py
"""

from __future__ import annotations

from typing import Any

from shared.domain.exceptions import RelationDomainError

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.sibling import SiblingRelation
from genealogy.domain.entities.spouse import SpouseRelation, create_spouse_relation
from genealogy.domain.enums import MarriageStatus


class SpousePolicy:
    """
    Проверяет инварианты перед созданием супружеской связи.

    Инварианты:
      1. Пара уже состоит в браке → нельзя добавить дубликат.
      2. Пара уже имеет запись о браке (не активном) → защита от случайного дублирования.
      3. Между этими людьми уже есть родительская связь → нельзя добавить брак.
      4. Эти люди — братья/сёстры → нельзя добавить брак.
    """

    def assert_can_add(
        self,
        person_a_id: str,
        person_b_id: str,
        existing_spouse_relations: list[SpouseRelation],
        existing_parent_relations: list[ParentChildRelation],
        existing_sibling_relations: list[SiblingRelation],
        marriage_status: MarriageStatus = MarriageStatus.MARRIED,
        **kwargs: Any,
    ) -> SpouseRelation:
        self._check_not_duplicate(person_a_id, person_b_id, existing_spouse_relations)
        self._check_not_already_parent_child(person_a_id, person_b_id, existing_parent_relations)
        self._check_not_siblings(person_a_id, person_b_id, existing_sibling_relations)

        return create_spouse_relation(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            marriage_status=marriage_status,
            **kwargs,
        )

    def _check_not_duplicate(
        self,
        person_a: str,
        person_b: str,
        existing: list[SpouseRelation],
    ) -> None:
        for rel in existing:
            if rel.involves(person_a) and rel.involves(person_b):
                if rel.is_active():
                    raise RelationDomainError(
                        message="Связь уже существует",
                        errors={"relation": "Эти люди уже состоят в браке."},
                    )
                else:
                    raise RelationDomainError(
                        message="Связь уже существует",
                        errors={
                            "relation": (
                                f"Запись об этом браке уже есть "
                                f"(статус: {rel.marriage_status.value}). "
                                "Для повторного брака добавьте новую запись после развода."
                            )
                        },
                    )

    def _check_not_already_parent_child(
        self,
        person_a: str,
        person_b: str,
        parent_relations: list[ParentChildRelation],
    ) -> None:
        for rel in parent_relations:
            if rel.involves(person_a) and rel.involves(person_b):
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={
                        "relation": (
                            "Нельзя добавить супружескую связь: между этими людьми уже есть родительская связь."
                        )
                    },
                )

    def _check_not_siblings(
        self,
        person_a: str,
        person_b: str,
        sibling_relations: list[SiblingRelation],
    ) -> None:
        for rel in sibling_relations:
            if rel.involves(person_a) and rel.involves(person_b):
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={"relation": ("Нельзя создать супружескую связь: эти люди являются братьями или сёстрами.")},
                )
