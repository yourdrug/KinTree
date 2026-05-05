"""
identity/domain/repositories/permission.py

Контракты репозиториев системы разрешений.

"""

from __future__ import annotations

from typing import Protocol

from identity.domain.entities.account_role import AccountRole
from identity.domain.entities.permission import Role
from identity.domain.value_objects.permission import Permission


class PermissionRepository(Protocol):
    """Контракт хранилища Permission'ов."""

    async def get_all(self) -> list[Permission]: ...

    async def get_by_codename(self, codename: str) -> Permission | None: ...

    async def get_by_codenames(self, codenames: list[str]) -> list[Permission]: ...

    async def create(self, permission: Permission) -> Permission: ...

    async def upsert_many(self, permissions: list[Permission]) -> list[Permission]:
        """INSERT OR UPDATE по codename. Используется при синхронизации при старте."""
        ...

    async def remove_all(self) -> None: ...


class RoleRepository(Protocol):
    """Контракт хранилища Role'ей."""

    async def get_all(self) -> list[Role]: ...

    async def get_by_name(self, name: str) -> Role | None: ...

    async def get_by_name_with_permissions(self, name: str) -> Role | None:
        """Роль с загруженными пермишенами. Один JOIN вместо N+1."""
        ...

    async def create(self, role: Role) -> Role: ...

    async def upsert_many(self, roles: list[Role]) -> list[Role]: ...

    async def set_permissions(self, role_id: str, permission_ids: list[str]) -> None:
        """Полная замена пермишенов роли. Атомарно в рамках UoW."""
        ...

    async def remove_all_role_permissions(self) -> None: ...

    async def remove_all(self) -> None: ...


class AccountRoleRepository(Protocol):
    """Контракт хранилища связей аккаунт → роль."""

    async def get_by_account_id(self, account_id: str) -> AccountRole | None: ...

    async def assign_role(self, account_role: AccountRole) -> AccountRole:
        """Upsert: если уже есть — обновить, нет — создать."""
        ...

    async def exists(self, account_id: str) -> bool: ...
