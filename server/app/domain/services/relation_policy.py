from __future__ import annotations

from typing import Any

from domain.entities.parent_child import ParentChildRelation
from domain.entities.spouse import SpouseRelation, create_spouse_relation
from domain.enums import MarriageStatus, RelationType
from domain.exceptions import DomainRelationError


class RelationPolicy:
    """
    Доменный сервис: проверяет инварианты связей между персонами.

    Проверки которые нельзя сделать в одном агрегате
    (затрагивают несколько персон и существующие связи).
    """

    # ── ParentChild ──────────────────────────────────────────────────────────

    def assert_can_add_parent_child(
        self,
        parent_id: str,
        child_id: str,
        relation_type: RelationType,
        existing_parent_relations: list[ParentChildRelation],
        existing_spouse_relations: list[SpouseRelation],
    ) -> ParentChildRelation:
        """
        Проверяет что можно добавить связь родитель–ребёнок.
        Возвращает готовый доменный объект.
        """
        self._check_not_duplicate_parent(parent_id, child_id, existing_parent_relations)
        self._check_not_already_spouse(parent_id, child_id, existing_spouse_relations)
        self._check_biological_parent_limit(child_id, relation_type, existing_parent_relations)

        return ParentChildRelation(
            parent_id=parent_id,
            child_id=child_id,
            relation_type=relation_type,
        )

    def _check_not_duplicate_parent(
        self,
        parent_id: str,
        child_id: str,
        existing: list[ParentChildRelation],
    ) -> None:
        """Эта конкретная пара (parent, child) уже существует."""
        for rel in existing:
            if rel.parent_id == parent_id and rel.child_id == child_id:
                raise DomainRelationError(
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
                raise DomainRelationError(
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
        Приёмных/отчимов — без ограничений.
        """
        if new_relation_type != RelationType.BIOLOGICAL:
            return

        bio_parents = [r for r in existing if r.child_id == child_id and r.relation_type == RelationType.BIOLOGICAL]

        if len(bio_parents) >= 2:
            raise DomainRelationError(
                message="Ошибка валидации",
                errors={"relation": ("У ребёнка уже есть 2 биологических родителя. Используйте тип ADOPTED или STEP.")},
            )

    # ── Spouse ───────────────────────────────────────────────────────────────

    def assert_can_add_spouse(
        self,
        person_a_id: str,
        person_b_id: str,
        existing_spouse_relations: list[SpouseRelation],
        existing_parent_relations: list[ParentChildRelation],
        marriage_status: MarriageStatus = MarriageStatus.MARRIED,
        **kwargs: Any,
    ) -> SpouseRelation:
        """
        Проверяет что можно добавить супружескую связь.
        Возвращает готовый доменный объект.
        """
        self._check_not_duplicate_spouse(person_a_id, person_b_id, existing_spouse_relations)
        self._check_not_already_parent_child(person_a_id, person_b_id, existing_parent_relations)

        return create_spouse_relation(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            marriage_status=marriage_status,
            **kwargs,
        )

    def _check_not_duplicate_spouse(
        self,
        person_a: str,
        person_b: str,
        existing: list[SpouseRelation],
    ) -> None:
        """Пара уже состоит в активном браке."""
        for rel in existing:
            if rel.involves(person_a) and rel.involves(person_b):
                if rel.is_active():
                    raise DomainRelationError(
                        message="Связь уже существует",
                        errors={"relation": "Эти люди уже состоят в браке."},
                    )
                else:
                    raise DomainRelationError(
                        message="Связь уже существует",
                        errors={
                            "relation": (
                                "Запись об этом браке уже есть "
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
        """Нельзя быть одновременно родителем и супругом."""
        for rel in parent_relations:
            if rel.involves(person_a) and rel.involves(person_b):
                raise DomainRelationError(
                    message="Ошибка валидации",
                    errors={
                        "relation": (
                            "Нельзя добавить супружескую связь: между этими людьми уже есть родительская связь."
                        )
                    },
                )
