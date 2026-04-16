"""
domain/repositories/permission.py

Контракты репозиториев системы разрешений.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.permission import PermissionEntity, RoleEntity


class AbstractPermissionRepository(ABC):
    @abstractmethod
    async def get_all_permissions(self) -> list[PermissionEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_permission_by_codename(self, codename: str) -> PermissionEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def create_permission(self, codename: str, description: str = "") -> PermissionEntity:
        raise NotImplementedError

    @abstractmethod
    async def ensure_permissions_exist(self, codenames: list[str]) -> list[PermissionEntity]:
        """Создаёт разрешения если их нет, возвращает все."""
        raise NotImplementedError


class AbstractRoleRepository(ABC):
    @abstractmethod
    async def get_all_roles(self) -> list[RoleEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_role_by_name(self, name: str) -> RoleEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_role_with_permissions(self, name: str) -> RoleEntity | None:
        """Загружает роль вместе с разрешениями."""
        raise NotImplementedError

    @abstractmethod
    async def create_role(self, name: str, description: str = "") -> RoleEntity:
        raise NotImplementedError

    @abstractmethod
    async def assign_permission_to_role(self, role_name: str, permission_codename: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_permission_from_role(self, role_name: str, permission_codename: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def set_role_permissions(self, role_name: str, permission_codenames: list[str]) -> RoleEntity:
        """Заменяет все разрешения роли на переданный список."""
        raise NotImplementedError

    @abstractmethod
    async def ensure_default_roles_exist(self) -> None:
        """Создаёт системные роли при старте приложения."""
        raise NotImplementedError


class AbstractAccountRoleRepository(ABC):
    @abstractmethod
    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        """Возвращает codename всех разрешений аккаунта через его роль."""
        raise NotImplementedError

    @abstractmethod
    async def set_account_role(self, account_id: str, role_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_account_role_name(self, account_id: str) -> str:
        raise NotImplementedError
    