"""
identity/domain/value_objects/permission.py

Permission — Value Object.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    """
    Value Object: атомарное право на действие.

    Идентичность — по codename (не id).
    Immutable: frozen=True.
    """

    id: str
    codename: str
    description: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return NotImplemented
        return self.codename == other.codename

    def __hash__(self) -> int:
        return hash(self.codename)

    def __str__(self) -> str:
        return self.codename
