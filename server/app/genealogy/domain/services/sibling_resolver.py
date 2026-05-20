"""
domain/services/sibling_resolver.py

Доменный сервис: определение типа сиблинговой связи.
"""

from __future__ import annotations

from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.sibling import SiblingRelation, SiblingType
from genealogy.domain.enums import RelationType


class SiblingResolver:
    """
    Вычисляет список сиблингов для заданной персоны
    на основе набора родительских связей.

    Алгоритм:
    1. Найти всех родителей person_id.
    2. Найти всех детей этих родителей (кроме самого person_id).
    3. Для каждого кандидата — определить общих родителей и SiblingType.
    4. Если кандидат встречается через нескольких родителей — берём
       наивысший приоритет (FULL > HALF > STEP).
    """

    # Приоритет типов: чем ниже число, тем "ближе" связь
    _PRIORITY: dict[SiblingType, int] = {
        SiblingType.FULL: 0,
        SiblingType.HALF: 1,
        SiblingType.STEP: 2,
    }

    def resolve(
        self,
        person_id: str,
        all_relations: list[ParentChildRelation],
    ) -> list[SiblingRelation]:
        """
        Вычисляет сиблинговые связи для person_id.

        Args:
            person_id:     ID персоны, для которой ищем братьев/сестёр.
            all_relations: все ParentChild-связи, где участвует person_id
                           или любой из его родителей/детей.
                           Репозиторий должен предоставить достаточный контекст.

        Returns:
            Список SiblingRelation (уникальных, без дубликатов).
        """
        # Шаг 1: родители person_id → {parent_id: relation_type}
        parents: dict[str, RelationType] = {
            r.parent_id: r.relation_type for r in all_relations if r.child_id == person_id
        }

        if not parents:
            return []

        # Шаг 2: дети каждого родителя → кандидаты в сиблинги
        # sibling_id → {parent_id: relation_type_for_person,
        #               relation_type_for_sibling}
        # Нам нужно знать:
        #   - тип связи person_id с этим родителем
        #   - тип связи sibling_id с этим родителем
        # Обе нужны для определения FULL/HALF/STEP

        # Собираем: sibling_id → список (parent_id, type_to_person, type_to_sibling)
        candidate_parents: dict[str, list[tuple[str, RelationType, RelationType]]] = {}

        for rel in all_relations:
            # rel: родитель → ребёнок
            if rel.parent_id not in parents:
                continue
            if rel.child_id == person_id:
                continue  # это сам person_id

            sibling_id = rel.child_id
            parent_id = rel.parent_id
            type_to_person = parents[parent_id]  # тип связи person с этим родителем
            type_to_sibling = rel.relation_type  # тип связи sibling с этим родителем

            candidate_parents.setdefault(sibling_id, []).append((parent_id, type_to_person, type_to_sibling))

        if not candidate_parents:
            return []

        # Шаг 3: для каждого кандидата вычислить SiblingType
        result: list[SiblingRelation] = []

        for sibling_id, parent_entries in candidate_parents.items():
            sibling_type, shared_ids = self._compute_type(parent_entries)
            result.append(
                SiblingRelation(
                    person_id=person_id,
                    sibling_id=sibling_id,
                    sibling_type=sibling_type,
                    shared_parent_ids=frozenset(shared_ids),
                )
            )

        return result

    def _compute_type(
        self,
        parent_entries: list[tuple[str, RelationType, RelationType]],
    ) -> tuple[SiblingType, list[str]]:
        """
        Определяет тип связи и список общих родителей.

        Логика:
        - Считаем биологических общих родителей (оба участника имеют BIO-связь)
        - 2+ общих BIO-родителя → FULL
        - 1  общий BIO-родитель  → HALF
        - 0  общих BIO-родителей → STEP (есть хотя бы один общий STEP/ADOPTED)
        """
        shared_ids = [pid for pid, _, _ in parent_entries]

        bio_shared = [
            pid
            for pid, type_to_person, type_to_sibling in parent_entries
            if type_to_person == RelationType.BIOLOGICAL and type_to_sibling == RelationType.BIOLOGICAL
        ]

        if len(bio_shared) >= 2:
            return SiblingType.FULL, shared_ids
        elif len(bio_shared) == 1:
            return SiblingType.HALF, shared_ids
        else:
            return SiblingType.STEP, shared_ids
