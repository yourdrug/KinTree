from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyRef:
    """
    Value Object: ссылка на Family из контекста Genealogy.

    Person хранит FamilyRef вместо голой строки family_id.
    Это делает зависимость явной и типобезопасной,
    не создавая прямой связи между агрегатами.
    """

    family_id: str

    def __post_init__(self) -> None:
        if not self.family_id or not self.family_id.strip():
            raise ValueError("family_id не может быть пустым")

    def __str__(self) -> str:
        return self.family_id