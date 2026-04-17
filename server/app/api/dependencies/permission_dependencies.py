"""
api/dependencies/permission_dependencies.py

FastAPI-зависимости для проверки разрешений.

Разрешения хранятся исключительно в БД и загружаются при аутентификации.

Паттерны использования:

  1. Depends(require_permission("family:create"))
     ─ Проверка по codename строкой

  2. Depends(require_any_permission(["family:create", "family:update_any"]))
     ─ Хотя бы одно из разрешений

  3. Depends(require_all_permissions(["family:create", "person:create"]))
     ─ Все разрешения обязательны

  4. Depends(require_role("admin"))
     ─ Проверка роли из JWT-клейма (без запроса в БД)

  5. check_owner_or_permission(account, "family:delete_any", owner_id)
     ─ Для проверок внутри handler'а после загрузки ресурса

Разрешения берутся из account.permissions (frozenset[str]),
который заполняется при аутентификации — никаких дополнительных
запросов в БД при каждом HTTP-запросе.
"""

from __future__ import annotations

from domain.entities.account import Account
from domain.exceptions import AuthenticationError
from fastapi import Depends

from api.dependencies.auth_dependencies import get_current_account


class _RequirePermission:
    """
    Dependency: требует наличия конкретного разрешения.

    Использование:
        account: Account = Depends(require_permission("family:create"))
    """

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
    """
    Dependency: требует хотя бы одно разрешение из списка.

    Использование:
        account: Account = Depends(require_any_permission(["admin:panel", "account:read_any"]))
    """

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
    """
    Dependency: требует все разрешения из списка.

    Использование:
        account: Account = Depends(require_all_permissions(["family:create", "person:create"]))
    """

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
    Dependency: требует конкретную роль из JWT-клейма.
    Не делает запрос в БД — роль читается из токена.

    Использование:
        account: Account = Depends(require_role("admin"))
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


def require_permission(codename: str) -> _RequirePermission:
    """
    Dependency-фабрика: проверяет наличие разрешения по codename.

    Пример:
        Depends(require_permission("family:create"))
    """
    return _RequirePermission(codename)


def require_any_permission(codenames: list[str]) -> _RequireAnyPermission:
    """
    Dependency-фабрика: хотя бы одно из разрешений.

    Пример:
        Depends(require_any_permission(["admin:panel", "account:read_any"]))
    """
    return _RequireAnyPermission(codenames)


def require_all_permissions(codenames: list[str]) -> _RequireAllPermissions:
    """
    Dependency-фабрика: все разрешения обязательны.

    Пример:
        Depends(require_all_permissions(["family:create", "person:create"]))
    """
    return _RequireAllPermissions(codenames)


def require_role(role_name: str) -> _RequireRole:
    """
    Dependency-фабрика: требует точное совпадение роли.

    Пример:
        Depends(require_role("admin"))
    """
    return _RequireRole(role_name)


def check_owner_or_permission(
    account: Account,
    codename: str,
    resource_owner_id: str,
) -> None:
    """
    Проверяет: текущий пользователь является владельцем ресурса
    ИЛИ имеет расширенное разрешение.

    Вызывается вручную внутри handler'а, когда owner_id известен
    только после загрузки ресурса из БД.

    Пример:
        family = await service.get_family(family_id)
        check_owner_or_permission(
            account=account,
            codename="family:delete_any",
            resource_owner_id=family.owner_id,
        )
        await service.delete_family(family_id)

    Raises:
        AuthenticationError — если не владелец и нет разрешения.
    """
    is_owner = account.id == resource_owner_id
    has_perm = account.has_permission(codename)

    if not is_owner and not has_perm:
        raise AuthenticationError(
            message="Недостаточно прав",
            errors={"detail": "Вы не являетесь владельцем этого ресурса"},
        )
