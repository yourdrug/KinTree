"""
domain/repositories/permission.py

Контракты репозиториев системы разрешений.

DDD-принципы:
- Protocol вместо ABC — структурное соответствие без наследования.
- Методы говорят на языке домена.
- Нет импортов инфраструктуры.
- Репозитории работают с доменными типами из domain/entities/permission.py.
"""

from __future__ import annotations

from typing import Protocol

from identity.domain.entities.permission import AccountRole, Permission, Role


class PermissionRepository(Protocol):
    """Контракт хранилища Permission'ов."""

    async def get_all(self) -> list[Permission]:
        """Все пермишены в системе."""
        ...

    async def get_by_codename(self, codename: str) -> Permission | None:
        """Найти по codename или вернуть None."""
        ...

    async def get_by_codenames(self, codenames: list[str]) -> list[Permission]:
        """Найти несколько пермишенов по codename (для пакетных операций)."""
        ...

    async def create(self, permission: Permission) -> Permission:
        """Создать новый пермишен. Raises ConflictError если codename занят."""
        ...

    async def upsert_many(self, permissions: list[Permission]) -> list[Permission]:
        """
        INSERT OR UPDATE для набора пермишенов.
        Используется при синхронизации при старте приложения.
        """
        ...

    async def remove_all(self) -> None:
        """Удалить все пермишены (для полной пересинхронизации)."""
        ...


class RoleRepository(Protocol):
    """Контракт хранилища Role'ей."""

    async def get_all(self) -> list[Role]:
        """Все роли в системе."""
        ...

    async def get_by_name(self, name: str) -> Role | None:
        """Найти по имени или вернуть None."""
        ...

    async def get_by_name_with_permissions(self, name: str) -> Role | None:
        """
        Найти роль с загруженными пермишенами.
        Один JOIN-запрос вместо N+1.
        """
        ...

    async def create(self, role: Role) -> Role:
        """Создать новую роль."""
        ...

    async def upsert_many(self, roles: list[Role]) -> list[Role]:
        """
        INSERT OR UPDATE для набора ролей.
        Используется при синхронизации при старте.
        """
        ...

    async def set_permissions(self, role_id: str, permission_ids: list[str]) -> None:
        """
        Полная замена набора пермишенов роли.
        DELETE всего старого + INSERT нового.
        Атомарно в рамках одной транзакции (UoW).
        """
        ...

    async def remove_all_role_permissions(self) -> None:
        """Удалить все связи роль-пермишен (для пересинхронизации)."""
        ...

    async def remove_all(self) -> None:
        """Удалить все роли."""
        ...


class AccountRoleRepository(Protocol):
    """Контракт хранилища связей аккаунт → роль."""

    async def get_by_account_id(self, account_id: str) -> AccountRole | None:
        """Связь аккаунт-роль или None если не назначена."""
        ...

    async def assign_role(self, account_role: AccountRole) -> AccountRole:
        """
        Назначить роль аккаунту.
        Upsert: если уже есть — обновить, нет — создать.
        """
        ...

    async def exists(self, account_id: str) -> bool:
        """Есть ли назначенная роль у аккаунта."""
        ...
