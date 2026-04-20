"""
application/family/services.py

Application-сервис для агрегата Family.

Принципы:
- Сервис получает зависимости явно через __init__.
- Работает через UnitOfWork, не через RepositoryFacade.
- PATCH/PUT применяются через приватные методы — чисто, без магии.
- Все публичные методы — use case'ы: одна операция = один метод.
"""

from __future__ import annotations

from typing import Any

from domain.entities.account import Account
from domain.entities.family import Family, create_family
from domain.exceptions import NotFoundError
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page
from domain.value_objects.unset import UnsetType

from application.family.commands import (
    CreateFamilyCommand,
    PatchFamilyCommand,
    PutFamilyCommand,
)
from application.uow_factory import UoWFactory


class FamilyService:
    """
    Application-сервис: управление агрегатом Family.

    Получает UoWFactory — фабрику Unit of Work.
    Каждый use case создаёт свой UoW (и транзакцию) через фабрику.
    """

    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    # ── Запросы ──────────────────────────────────────────────────────────────

    async def get_family(self, family_id: str) -> Family:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.families.get_by_id(family_id)

    async def get_families_list(self, spec: BaseFilterSpec) -> Page[Family]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.families.list(spec)

    # ── Команды ──────────────────────────────────────────────────────────────

    async def create_family(self, command: CreateFamilyCommand, account: Account) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            family = create_family(
                name=command.name,
                owner_id=account.id,
                description=command.description,
                origin_place=command.origin_place,
                founded_year=command.founded_year,
                ended_year=command.ended_year,
            )
            return await uow.families.save(family)

    async def update_family(self, command: PutFamilyCommand) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            existing = await uow.families.get_by_id_or_none(command.family_id)

            if existing is None or existing.owner_id != command.owner_id:
                raise NotFoundError(resource="Family", resource_id=command.family_id)

            updated = _apply_put(command, existing)
            return await uow.families.save(updated)

    async def patch_update_family(self, command: PatchFamilyCommand) -> Family:
        async with self._uow_factory.create(master=True) as uow:
            existing = await uow.families.get_by_id(command.family_id)
            updated = _apply_patch(command, existing)
            return await uow.families.save(updated)

    async def delete_family(self, family_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            await uow.families.remove(family_id)


# ── Чистые функции для PUT/PATCH ──────────────────────────────────────────────


def _resolve(new: Any, old: Any) -> Any:
    """Если new = UNSET — берём старое значение, иначе новое (даже если None)."""
    return old if isinstance(new, UnsetType) else new


def _apply_put(command: PutFamilyCommand, existing: Family) -> Family:
    """Полная замена данных семьи. owner_id сохраняется из существующей записи."""
    return Family(
        id=existing.id,
        name=command.name,
        owner_id=existing.owner_id,
        description=command.description,
        origin_place=command.origin_place,
        founded_year=command.founded_year,
        ended_year=command.ended_year,
        members=existing.members,
    )


def _apply_patch(command: PatchFamilyCommand, existing: Family) -> Family:
    """Частичное обновление семьи. UNSET-поля не изменяются."""
    return Family(
        id=existing.id,
        name=_resolve(command.name, existing.name),
        owner_id=existing.owner_id,
        description=_resolve(command.description, existing.description),
        origin_place=_resolve(command.origin_place, existing.origin_place),
        founded_year=_resolve(command.founded_year, existing.founded_year),
        ended_year=_resolve(command.ended_year, existing.ended_year),
        members=existing.members,
    )
