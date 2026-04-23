"""
domain/services/spouse_policy.py

Доменный сервис: инварианты супружеских связей.

SRP: этот класс отвечает ТОЛЬКО за проверки spouse.
Перекрёстная проверка «нельзя быть одновременно супругом и родителем»
присутствует здесь — это инвариант с точки зрения супружеской связи.
ParentChildPolicy содержит зеркальную проверку со своей стороны.
"""

from __future__ import annotations

from typing import Any

from shared.domain.exceptions import RelationDomainError

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.spouse import SpouseRelation, create_spouse_relation
from genealogy.domain.enums import MarriageStatus


class SpousePolicy:
    """
    Проверяет инварианты перед созданием супружеской связи.

    Инварианты:
      1. Пара уже состоит в активном браке → нельзя добавить дубликат.
      2. Пара уже имеет запись о браке (не активном) → нельзя создать новую
         без явного указания (защита от случайного дублирования).
      3. Между этими людьми уже есть родительская связь → нельзя добавить брак.
    """

    def assert_can_add(
        self,
        person_a_id: str,
        person_b_id: str,
        existing_spouse_relations: list[SpouseRelation],
        existing_parent_relations: list[ParentChildRelation],
        marriage_status: MarriageStatus = MarriageStatus.MARRIED,
        **kwargs: Any,
    ) -> SpouseRelation:
        """
        Проверяет все инварианты и возвращает готовый доменный объект.

        Args:
            person_a_id: ID первого человека.
            person_b_id: ID второго человека.
            existing_spouse_relations: уже существующие браки
                (достаточно загрузить те, где участвует хотя бы один из двоих).
            existing_parent_relations: уже существующие родительские связи
                (для перекрёстной проверки).
            marriage_status: статус создаваемого брака.
            **kwargs: дополнительные поля SpouseRelation (даты, место и т.д.).

        Returns:
            SpouseRelation — готовый объект в канонической форме, который
            можно персистировать.

        Raises:
            RelationDomainError: если любой инвариант нарушен.
        """
        self._check_not_duplicate(person_a_id, person_b_id, existing_spouse_relations)
        self._check_not_already_parent_child(person_a_id, person_b_id, existing_parent_relations)

        return create_spouse_relation(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            marriage_status=marriage_status,
            **kwargs,
        )

    # ── Приватные проверки ────────────────────────────────────────────────────

    def _check_not_duplicate(
        self,
        person_a: str,
        person_b: str,
        existing: list[SpouseRelation],
    ) -> None:
        """
        Пара уже состоит в активном браке или имеет запись о прошлом браке.
        """
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
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={
                        "relation": (
                            "Нельзя добавить супружескую связь: между этими людьми уже есть родительская связь."
                        )
                    },
                )
