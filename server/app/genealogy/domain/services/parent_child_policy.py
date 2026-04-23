"""
domain/services/parent_child_policy.py

Доменный сервис: инварианты родительских связей.

SRP: этот класс отвечает ТОЛЬКО за проверки parent-child.
Перекрёстная проверка «нельзя быть одновременно родителем и супругом»
присутствует здесь — это инвариант с точки зрения parent-child связи.
SpousePolicy содержит зеркальную проверку со своей стороны.
Это не дублирование — каждый агрегат защищает свой инвариант.
"""

from __future__ import annotations

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.spouse import SpouseRelation
from genealogy.domain.enums import RelationType
from shared.domain.exceptions import RelationDomainError


class ParentChildPolicy:
    """
    Проверяет инварианты перед созданием родительской связи.

    Инварианты:
      1. Пара (parent_id, child_id) уже существует → нельзя добавить дубликат.
      2. Эти двое уже состоят в браке → нельзя добавить родительскую связь.
      3. У ребёнка уже есть 2 биологических родителя → нельзя добавить ещё одного BIOLOGICAL.
    """

    def assert_can_add(
        self,
        parent_id: str,
        child_id: str,
        relation_type: RelationType,
        existing_parent_relations: list[ParentChildRelation],
        existing_spouse_relations: list[SpouseRelation],
    ) -> ParentChildRelation:
        """
        Проверяет все инварианты и возвращает готовый доменный объект.

        Args:
            parent_id: ID предполагаемого родителя.
            child_id: ID предполагаемого ребёнка.
            relation_type: тип связи (BIOLOGICAL / ADOPTED / STEP).
            existing_parent_relations: уже существующие parent-child связи
                (достаточно загрузить те, где участвует хотя бы один из двоих).
            existing_spouse_relations: уже существующие супружеские связи
                (для перекрёстной проверки).

        Returns:
            ParentChildRelation — готовый объект, который можно персистировать.

        Raises:
            RelationDomainError: если любой инвариант нарушен.
        """
        self._check_not_duplicate(parent_id, child_id, existing_parent_relations)
        self._check_not_already_spouse(parent_id, child_id, existing_spouse_relations)
        self._check_biological_parent_limit(child_id, relation_type, existing_parent_relations)

        return ParentChildRelation(
            parent_id=parent_id,
            child_id=child_id,
            relation_type=relation_type,
        )

    # ── Приватные проверки ────────────────────────────────────────────────────

    def _check_not_duplicate(
        self,
        parent_id: str,
        child_id: str,
        existing: list[ParentChildRelation],
    ) -> None:
        """Эта конкретная пара (parent, child) уже существует."""
        for rel in existing:
            if rel.parent_id == parent_id and rel.child_id == child_id:
                raise RelationDomainError(
                    message="Связь уже существует",
                    errors={"relation": "Эта родительская связь уже добавлена."},
                )

    def _check_not_already_spouse(
        self,
        person_a: str,
        person_b: str,
        spouse_relations: list[SpouseRelation],
    ) -> None:
        """Нельзя одновременно быть родителем и супругом одного человека."""
        for rel in spouse_relations:
            if rel.involves(person_a) and rel.involves(person_b):
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={"relation": ("Нельзя добавить родительскую связь: эти люди уже состоят в браке.")},
                )

    def _check_biological_parent_limit(
        self,
        child_id: str,
        new_relation_type: RelationType,
        existing: list[ParentChildRelation],
    ) -> None:
        """
        У ребёнка может быть не более 2 биологических родителей.
        Приёмных / отчимов — без ограничений.
        """
        if new_relation_type != RelationType.BIOLOGICAL:
            return

        bio_parents = [r for r in existing if r.child_id == child_id and r.relation_type == RelationType.BIOLOGICAL]

        if len(bio_parents) >= 2:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"relation": "У ребёнка уже есть 2 биологических родителя. Используйте тип ADOPTED или STEP."},
            )
