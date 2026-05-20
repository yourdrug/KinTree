"""
domain/entities/sibling.py

SiblingRelation — производная связь братьев/сестёр.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SiblingType(Enum):
    """
    Тип сиблинговой связи.

    FULL  — полные братья/сёстры (оба биологических родителя общие).
    HALF  — единокровные/единоутробные (один общий биологический родитель).
    STEP  — сводные (общий только приёмный родитель / отчим / мачеха).
    """

    FULL = "FULL"
    HALF = "HALF"
    STEP = "STEP"


@dataclass(frozen=True)
class SiblingRelation:
    """
    Производная связь: братья/сёстры.

    person_id      — субъект запроса
    sibling_id     — брат или сестра
    sibling_type   — тип связи (FULL / HALF / STEP)
    shared_parent_ids — ID общих родителей (для отладки и UI)

    Инвариант: person_id != sibling_id, оба непустые.
    """

    person_id: str
    sibling_id: str
    sibling_type: SiblingType
    shared_parent_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not self.person_id or not self.person_id.strip():
            raise ValueError("person_id cannot be empty")
        if not self.sibling_id or not self.sibling_id.strip():
            raise ValueError("sibling_id cannot be empty")
        if self.person_id == self.sibling_id:
            raise ValueError("person_id and sibling_id must differ")

    def involves(self, person_id: str) -> bool:
        return self.person_id == person_id or self.sibling_id == person_id

    def other(self, person_id: str) -> str:
        """Возвращает ID другого участника связи."""
        if self.person_id == person_id:
            return self.sibling_id
        if self.sibling_id == person_id:
            return self.person_id
        raise ValueError(f"Person {person_id!r} is not part of this sibling relation")
