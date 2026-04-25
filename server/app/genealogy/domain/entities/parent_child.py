from __future__ import annotations

from dataclasses import dataclass

from shared.domain.exceptions import RelationDomainError

from genealogy.domain.enums import RelationType


@dataclass(frozen=True)
class ParentChildRelation:
    """
    Value Object: связь родитель–ребёнок.

    frozen=True — связь неизменяема после создания.
    Для смены типа (BIOLOGICAL→ADOPTED) — удаляем старую, создаём новую.

    Инварианты:
    - parent_id != child_id
    - оба ID непустые строки длиной >= 32
    """

    parent_id: str
    child_id: str
    relation_type: RelationType

    def __post_init__(self) -> None:
        if not self.parent_id or not self.parent_id.strip():
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"parent_id": "ID родителя не может быть пустым."},
            )

        if not self.child_id or not self.child_id.strip():
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"child_id": "ID ребёнка не может быть пустым."},
            )

        if self.parent_id == self.child_id:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"ids": "Человек не может быть родителем самого себя."},
            )

        if not isinstance(self.relation_type, RelationType):
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"relation_type": "Некорректный тип связи."},
            )

    def involves(self, person_id: str) -> bool:
        """Участвует ли персона в этой связи."""
        return self.parent_id == person_id or self.child_id == person_id

    def is_parent_of(self, child_id: str) -> bool:
        return self.child_id == child_id

    def is_child_of(self, parent_id: str) -> bool:
        return self.parent_id == parent_id

    def with_type(self, new_type: RelationType) -> ParentChildRelation:
        """
        Возвращает новую связь с изменённым типом.
        Иммутабельная альтернатива change_type().
        """
        return ParentChildRelation(
            parent_id=self.parent_id,
            child_id=self.child_id,
            relation_type=new_type,
        )
