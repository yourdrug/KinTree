"""
identity/domain/entities/account_role.py

AccountRole — Entity, не Value Object.

Причина: имеет суррогатный id, используется для upsert в БД.
Value Object идентифицируется по значению, Entity — по id.

Перенесён из domain/value_objects/ в domain/entities/ для корректной DDD-классификации.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.utils import generate_uuid


@dataclass
class AccountRole:
    """
    Entity: связь аккаунт → роль.
    Один аккаунт имеет ровно одну роль.
    """

    id: str
    account_id: str
    role_id: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AccountRole):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


def create_account_role(account_id: str, role_id: str) -> AccountRole:
    """Фабрика AccountRole. Генерирует id."""
    return AccountRole(
        id=generate_uuid(),
        account_id=account_id,
        role_id=role_id,
    )
