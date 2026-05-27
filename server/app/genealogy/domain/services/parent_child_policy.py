"""
genealogy/domain/services/parent_child_policy.py

Доменный сервис: инварианты родительских связей.

Изменения v2:
  - Разделена проверка BIO-лимита: сообщение теперь содержит, сколько
    биологических родителей уже есть, чтобы пользователь понял почему отказ.
  - Добавлена проверка на «обратную» связь: нельзя сделать A родителем B,
    если B уже (прямо или косвенно) является родителем A (цикл).
    Простая проверка глубиной 1 — без полного обхода графа, т.к. полная
    проверка циклов слишком дорога для policy и лучше делается на уровне
    инфраструктуры через UNIQUE + FK.
  - Добавлена проверка: нельзя быть своим собственным родителем.
  - STEP-родитель уже является супругом биологического родителя —
    теперь это НЕ блокируется (допустимый edge-кейс: отчим добавляется
    как STEP для детей жены). Policy проверяет только прямой parent-spouse
    конфликт (один человек = и родитель, и супруг одного и того же человека).
"""

from __future__ import annotations

from shared.domain.exceptions import RelationDomainError

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.spouse import SpouseRelation
from genealogy.domain.enums import RelationType


class ParentChildPolicy:
    """
    Проверяет инварианты перед созданием родительской связи.

    Инварианты:
      1. Self-loop: нельзя быть родителем самого себя.
      2. Дубликат: пара (parent_id, child_id) уже существует.
      3. Перевёрнутая связь: child уже является родителем parent (прямой цикл).
      4. Супруги: parent и child уже состоят в браке (прямой конфликт ролей).
      5. Лимит BIO-родителей: у ребёнка уже 2 биологических родителя.
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
            parent_id:                 ID предполагаемого родителя.
            child_id:                  ID предполагаемого ребёнка.
            relation_type:             BIO | ADOPTED | STEP.
            existing_parent_relations: parent-child связи, где участвует
                                       хотя бы один из двоих.
            existing_spouse_relations: супружеские связи для кросс-проверки.

        Returns:
            ParentChildRelation — готовый объект для персистирования.

        Raises:
            RelationDomainError: если любой инвариант нарушен.
        """
        self._check_not_self(parent_id, child_id)
        self._check_not_duplicate(parent_id, child_id, existing_parent_relations)
        self._check_not_inverted(parent_id, child_id, existing_parent_relations)
        self._check_not_already_spouse(parent_id, child_id, existing_spouse_relations)
        self._check_biological_parent_limit(child_id, relation_type, existing_parent_relations)

        return ParentChildRelation(
            parent_id=parent_id,
            child_id=child_id,
            relation_type=relation_type,
        )

    # ── Проверки ──────────────────────────────────────────────────────────────

    def _check_not_self(self, parent_id: str, child_id: str) -> None:
        if parent_id == child_id:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"relation": "Персона не может быть своим собственным родителем."},
            )

    def _check_not_duplicate(
        self,
        parent_id: str,
        child_id: str,
        existing: list[ParentChildRelation],
    ) -> None:
        for rel in existing:
            if rel.parent_id == parent_id and rel.child_id == child_id:
                raise RelationDomainError(
                    message="Связь уже существует",
                    errors={"relation": "Эта родительская связь уже добавлена."},
                )

    def _check_not_inverted(
        self,
        parent_id: str,
        child_id: str,
        existing: list[ParentChildRelation],
    ) -> None:
        """
        Прямая проверка инверсии: child уже является родителем parent.

        Это предотвращает «ближний» цикл (глубина 1).
        Полный цикл (A→B→C→A) не проверяется здесь — это задача инфраструктуры.
        """
        for rel in existing:
            if rel.parent_id == child_id and rel.child_id == parent_id:
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={
                        "relation": (
                            "Нельзя создать связь: выбранный ребёнок уже является "
                            "родителем выбранного родителя. Это создало бы цикл."
                        )
                    },
                )

    def _check_not_already_spouse(
        self,
        person_a: str,
        person_b: str,
        spouse_relations: list[SpouseRelation],
    ) -> None:
        """
        Нельзя одновременно быть родителем и супругом одного человека.

        Edge-кейс: отчим (C) женат на матери (B) ребёнка (A).
        Здесь C → A добавляется как STEP, но C и B уже супруги — это OK.
        Policy проверяет только прямую пару (parent_id, child_id),
        то есть запрещает: C является одновременно и родителем B, и супругом B.
        """
        for rel in spouse_relations:
            if rel.involves(person_a) and rel.involves(person_b):
                raise RelationDomainError(
                    message="Ошибка валидации",
                    errors={
                        "relation": (
                            "Нельзя добавить родительскую связь: "
                            "эти люди уже состоят в браке."
                        )
                    },
                )

    def _check_biological_parent_limit(
        self,
        child_id: str,
        new_relation_type: RelationType,
        existing: list[ParentChildRelation],
    ) -> None:
        """
        У ребёнка может быть не более 2 биологических родителей.

        ADOPTED и STEP — без ограничений по количеству.
        Добавление ADOPTED/STEP при 2 уже имеющихся BIO-родителях разрешено.
        """
        if new_relation_type != RelationType.BIOLOGICAL:
            return

        bio_parents = [
            r for r in existing
            if r.child_id == child_id and r.relation_type == RelationType.BIOLOGICAL
        ]

        count = len(bio_parents)
        if count >= 2:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={
                    "relation": (
                        f"У ребёнка уже {count} биологических родителя(-ей). "
                        "Для добавления ещё одного родителя используйте тип "
                        "ADOPTED (приёмный) или STEP (отчим/мачеха)."
                    )
                },
            )
        