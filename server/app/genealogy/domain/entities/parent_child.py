from __future__ import annotations

from dataclasses import dataclass

from genealogy.domain.enums import RelationType
from shared.domain.exceptions import RelationDomainError


@dataclass
class ParentChildRelation:
    """
    Value Object: связь родитель–ребёнок.

    Frozen=True — связь неизменяема после создания.
    Для смены типа (BIOLOGICAL→ADOPTED) — удаляем старую, создаём новую.

    Инварианты:
    - parent_id != child_id
    - оба ID непустые
    """

    parent_id: str
    child_id: str
    relation_type: RelationType

    def __post_init__(self) -> None:
        if not self.parent_id or not self.child_id:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"ids": "ID родителя и ребёнка не могут быть пустыми."},
            )
        if self.parent_id == self.child_id:
            raise RelationDomainError(
                message="Ошибка валидации",
                errors={"ids": "Человек не может быть родителем самого себя."},
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParentChildRelation):
            return NotImplemented
        return self.parent_id == other.parent_id and self.child_id == other.child_id

    def __hash__(self) -> int:
        return hash((self.parent_id, self.child_id))

    def involves(self, person_id: str) -> bool:
        """Участвует ли персона в этой связи."""
        return self.parent_id == person_id or self.child_id == person_id

    def is_parent_of(self, child_id: str) -> bool:
        return self.child_id == child_id

    def is_child_of(self, parent_id: str) -> bool:
        return self.parent_id == parent_id

    def change_type(self, new_type: RelationType) -> None:
        """Mutation method — изменение типа связи."""
        self.relation_type = new_type
