"""
api/dependencies/permission_dependencies.py

FastAPI-зависимости для проверки разрешений.

Три паттерна использования:

  1. Depends(Permission.FAMILY__CREATE)
     ─ Через __call__ на строковом enum — самый компактный синтаксис

  2. Depends(require_permission("family:create"))
     ─ Для случаев когда codename — строка

  3. Depends(require_role("admin"))
     ─ Проверка роли из JWT-клейма (без запроса в БД)

  4. check_owner_or_permission(account, "family:delete_any", owner_id)
     ─ Для проверок внутри handler'а после загрузки ресурса

Разрешения берутся из account.permissions (frozenset[str]),
который заполняется при аутентификации — никаких дополнительных
запросов в БД при каждом HTTP-запросе.
"""

from __future__ import annotations

from domain.entities.account import Account
from domain.exceptions import AuthenticationError
from domain.permissions.enums import Permission
from fastapi import Depends

from api.dependencies.auth_dependencies import get_current_account


# ── Вспомогательные callable-классы ───────────────────────────────────────


class _RequirePermission:
    """
    Dependency: требует наличия конкретного разрешения.

    Использование:
        account: Account = Depends(require_permission(Permission.FAMILY__CREATE))
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
        account: Account = Depends(require_any_permission([Permission.ADMIN__PANEL, Permission.ACCOUNT__READ_ANY]))
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


# ── Публичные фабрики ──────────────────────────────────────────────────────


def require_permission(permission: Permission | str) -> _RequirePermission:
    """
    Dependency-фабрика: проверяет наличие разрешения.

    Принимает Permission enum или строку:
        Depends(require_permission(Permission.FAMILY__CREATE))
        Depends(require_permission("family:create"))
    """
    codename = permission.value if isinstance(permission, Permission) else permission
    return _RequirePermission(codename)


def require_any_permission(permissions: list[Permission | str]) -> _RequireAnyPermission:
    """
    Dependency-фабрика: хотя бы одно из разрешений.

    Пример:
        Depends(require_any_permission([Permission.ADMIN__PANEL, Permission.ACCOUNT__READ_ANY]))
    """
    codenames = [p.value if isinstance(p, Permission) else p for p in permissions]
    return _RequireAnyPermission(codenames)


def require_role(role_name: str) -> _RequireRole:
    """
    Dependency-фабрика: требует точное совпадение роли.

    Пример:
        Depends(require_role("admin"))
    """
    return _RequireRole(role_name)


# ── Утилита для проверки внутри handler'а ─────────────────────────────────


def check_owner_or_permission(
    account: Account,
    permission: Permission | str,
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
            permission=Permission.FAMILY__DELETE_ANY,
            resource_owner_id=family.owner_id,
        )
        await service.delete_family(family_id)

    Raises:
        AuthenticationError — если не владелец и нет разрешения.
    """
    is_owner = account.id == resource_owner_id
    codename = permission.value if isinstance(permission, Permission) else permission
    has_perm = account.has_permission(codename)

    if not is_owner and not has_perm:
        raise AuthenticationError(
            message="Недостаточно прав",
            errors={"detail": "Вы не являетесь владельцем этого ресурса"},
        )
