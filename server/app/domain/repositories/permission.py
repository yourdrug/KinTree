"""
domain/repositories/permission.py

Контракты репозиториев системы разрешений.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.permission import (
    AccountRoleEntity,
    PermissionEntity,
    RoleEntity,
    RolePermissionEntity,
)


class AbstractPermissionRepository(ABC):
    @abstractmethod
    async def get_all_permissions(self) -> list[PermissionEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_permission_or_none(self, codename: str) -> PermissionEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def create_permission(self, permission: PermissionEntity) -> PermissionEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete_all_permissions(self) -> None:
        raise NotImplementedError


class AbstractRoleRepository(ABC):
    @abstractmethod
    async def get_all_roles(self) -> list[RoleEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_role_or_none(self, name: str) -> RoleEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_role_with_permissions(self, name: str) -> RoleEntity | None:
        """Загружает роль вместе с разрешениями."""
        raise NotImplementedError

    @abstractmethod
    async def create_role(self, role_entity: RoleEntity) -> RoleEntity:
        raise NotImplementedError

    @abstractmethod
    async def create_role_permissions(self, role_permission: RolePermissionEntity) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all_role_permission(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all_roles(self) -> None:
        raise NotImplementedError


class AbstractAccountRoleRepository(ABC):
    @abstractmethod
    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        """Возвращает codename всех разрешений аккаунта через его роль."""
        raise NotImplementedError

    @abstractmethod
    async def set_account_role(self, account_role: AccountRoleEntity) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_account_role_name(self, account_id: str) -> str:
        raise NotImplementedError
