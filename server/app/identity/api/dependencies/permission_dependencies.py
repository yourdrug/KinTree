"""
api/dependencies/permission_dependencies.py

FastAPI-зависимости для проверки разрешений.

Разрешения хранятся в БД и загружаются при аутентификации.
Account.permissions — frozenset[str] codename'ов.

Паттерны использования:

  1. Depends(require_permission("family:create"))
     ─ Проверка одного пермишена по codename

  2. Depends(require_any_permission(["family:create", "family:update:any"]))
     ─ Хотя бы один из пермишенов

  3. Depends(require_all_permissions(["family:create", "person:create"]))
     ─ Все пермишены обязательны

  4. Depends(require_role("admin"))
     ─ Проверка роли из JWT-клейма (без запроса в БД)

  5. check_owner_or_permission(account, "family:delete:any", owner_id)
     ─ Для проверок внутри handler'а после загрузки ресурса

Можно использовать константы из PermissionCodename для избежания хардкода строк:
  from domain.permissions.enums import PermissionCodename
  Depends(require_permission(PermissionCodename.FAMILY__CREATE))
"""

from __future__ import annotations

from fastapi import Depends
from shared.domain.exceptions import AuthenticationError

from identity.api.dependencies.auth_dependencies import get_current_account
from identity.domain.entities.account import Account
from identity.domain.permissions.enums import PermissionCodename


class _RequirePermission:
    """Dependency: требует наличия конкретного пермишена."""

    __slots__ = ("_codename",)

    def __init__(self, codename: str) -> None:
        self._codename = codename

    async def __call__(
        self,
        account: Account = Depends(get_current_account),
    ) -> Account:
        if not account.has_permission(self._codename):
            raise AuthenticationError(
                message="Недостаточно прав",
                errors={"required_permission": self._codename},
            )
        return account


class _RequireAnyPermission:
    """Dependency: требует хотя бы один пермишен из списка."""

    __slots__ = ("_codenames",)

    def __init__(self, codenames: list[str]) -> None:
        self._codenames = codenames

    async def __call__(
        self,
        account: Account = Depends(get_current_account),
    ) -> Account:
        if not account.has_any_permission(self._codenames):
            raise AuthenticationError(
                message="Недостаточно прав",
                errors={"required_any_of": self._codenames},
            )
        return account


class _RequireAllPermissions:
    """Dependency: требует все пермишены из списка."""

    __slots__ = ("_codenames",)

    def __init__(self, codenames: list[str]) -> None:
        self._codenames = codenames

    async def __call__(
        self,
        account: Account = Depends(get_current_account),
    ) -> Account:
        if not account.has_all_permissions(self._codenames):
            raise AuthenticationError(
                message="Недостаточно прав",
                errors={"required_all_of": self._codenames},
            )
        return account


class _RequireRole:
    """
    Dependency: требует конкретную роль.
    Читает роль из Account.role_name — без запроса в БД.
    """

    __slots__ = ("_role_name",)

    def __init__(self, role_name: str) -> None:
        self._role_name = role_name

    async def __call__(
        self,
        account: Account = Depends(get_current_account),
    ) -> Account:
        if account.role_name != self._role_name:
            raise AuthenticationError(
                message="Недостаточно прав",
                errors={"required_role": self._role_name},
            )
        return account


# ── Фабричные функции (публичный API зависимостей) ────────────────────────────


def require_permission(codename: str | PermissionCodename) -> _RequirePermission:
    """
    Dependency-фабрика: проверяет наличие пермишена по codename.

    Пример:
        Depends(require_permission(PermissionCodename.FAMILY__CREATE))
        Depends(require_permission("family:create"))
    """
    return _RequirePermission(str(codename))


def require_any_permission(codenames: list[str | PermissionCodename]) -> _RequireAnyPermission:
    """
    Dependency-фабрика: хотя бы один пермишен из списка.

    Пример:
        Depends(require_any_permission([PermissionCodename.ADMIN__PANEL, PermissionCodename.ACCOUNT__READ_ANY]))
    """
    return _RequireAnyPermission([str(c) for c in codenames])


def require_all_permissions(codenames: list[str | PermissionCodename]) -> _RequireAllPermissions:
    """
    Dependency-фабрика: все пермишены обязательны.

    Пример:
        Depends(require_all_permissions([PermissionCodename.FAMILY__CREATE, PermissionCodename.PERSON__CREATE]))
    """
    return _RequireAllPermissions([str(c) for c in codenames])


def require_role(role_name: str) -> _RequireRole:
    """
    Dependency-фабрика: требует точное совпадение роли.

    Пример:
        Depends(require_role("admin"))
    """
    return _RequireRole(role_name)


def check_owner_or_permission(
    account: Account,
    codename: str | PermissionCodename,
    resource_owner_id: str,
) -> None:
    """
    Вспомогательная функция (не Depends):
    проверяет, что текущий пользователь является владельцем ресурса
    ИЛИ имеет расширенный пермишен.

    Вызывается вручную внутри handler'а, когда owner_id известен
    только после загрузки ресурса из БД.

    Пример:
        family = await service.get_family(family_id)
        check_owner_or_permission(
            account=account,
            codename=PermissionCodename.FAMILY__DELETE_ANY,
            resource_owner_id=family.owner_id,
        )
        await service.delete_family(family_id)

    Raises:
        AuthenticationError если не владелец и нет пермишена.
    """
    is_owner = account.id == resource_owner_id
    has_perm = account.has_permission(str(codename))

    if not is_owner and not has_perm:
        raise AuthenticationError(
            message="Недостаточно прав",
            errors={"detail": "Вы не являетесь владельцем этого ресурса"},
        )
