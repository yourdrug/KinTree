"""
application/person/service.py

Application-сервис для агрегата Person.

Принципы:
- Сервис не наследует BaseService — получает зависимости явно через __init__.
- Работает через UnitOfWork, не через RepositoryFacade.
- Бизнес-логика сборки агрегата инкапсулирована в _load_family_with_members().
- PATCH применяется через функцию _apply_patch() — чисто, без магии.
- Все публичные методы — use case'ы: одна операция = один метод.
"""

from __future__ import annotations

from typing import Any

from domain.entities.family import Family
from domain.entities.person import Person, create_person
from domain.filters.base import BaseFilterSpec
from domain.repositories.person import Page
from domain.value_objects.name import PersonName
from domain.value_objects.unset import UnsetType

from application.person.commands import CreatePersonCommand, PatchPersonCommand, UpdatePersonCommand
from application.uow_factory import UoWFactory


class PersonService:
    """
    Application-сервис: управление агрегатом Person.

    Получает UoWFactory — фабрику Unit of Work.
    Каждый use case создаёт свой UoW (и транзакцию) через фабрику.
    """

    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    # ── Запросы ──────────────────────────────────────────────────────────────

    async def get_person(self, person_id: str) -> Person:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.persons.get_by_id(person_id)

    async def list_persons(self, spec: BaseFilterSpec) -> Page[Person]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.persons.list(spec)

    # ── Команды ──────────────────────────────────────────────────────────────

    async def create_person(self, command: CreatePersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            family = await self._load_family_with_members(uow, command.family_id)

            person = create_person(
                gender=command.gender,
                family_id=command.family_id,
                first_name=command.first_name,
                last_name=command.last_name,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            # Доменный инвариант: семья разрешает добавление
            family.assert_can_add_member(person)

            return await uow.persons.save(person)

    async def update_person(self, command: UpdatePersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            existing = await uow.persons.get_by_id(command.person_id)

            updated = Person(
                id=existing.id,
                family_id=existing.family_id,
                name=PersonName(first_name=command.first_name, last_name=command.last_name),
                gender=command.gender,
                birth_date=command.birth_date,
                death_date=command.death_date,
                birth_date_raw=command.birth_date_raw,
                death_date_raw=command.death_date_raw,
            )

            family = await self._load_family_with_members(uow, existing.family_id, exclude_id=existing.id)
            family.assert_can_add_member(updated)

            return await uow.persons.save(updated)

    async def patch_person(self, command: PatchPersonCommand) -> Person:
        async with self._uow_factory.create(master=True) as uow:
            existing = await uow.persons.get_by_id(command.person_id)
            updated = _apply_patch(command, existing)

            if _patch_affects_identity(command):
                family = await self._load_family_with_members(uow, existing.family_id, exclude_id=existing.id)
                family.assert_can_add_member(updated)

            return await uow.persons.save(updated)

    async def delete_person(self, person_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            await uow.persons.remove(person_id)

    # ── Приватные хелперы ─────────────────────────────────────────────────────

    @staticmethod
    async def _load_family_with_members(
        uow: Any,
        family_id: str,
        exclude_id: str | None = None,
    ) -> Family:
        """
        Загружает агрегат Family вместе со списком членов.
        exclude_id — исключает конкретного члена (при update, чтобы не сравнивать с собой).
        """
        family = await uow.families.get_by_id(family_id)
        members = await uow.persons.find_by_family(family_id)
        family.members = [m for m in members if m.id != exclude_id] if exclude_id else members
        return family


# ── Чистые функции для патча ──────────────────────────────────────────────────


def _resolve(new: Any, old: Any) -> Any:
    """Если new = UNSET — берём старое значение, иначе новое (даже если None)."""
    return old if isinstance(new, UnsetType) else new


def _apply_patch(command: PatchPersonCommand, existing: Person) -> Person:
    """
    Применяет PATCH-команду к существующей персоне.
    Возвращает новый объект Person (existing не мутируется).
    """
    first_name = _resolve(command.first_name, existing.first_name)
    last_name = _resolve(command.last_name, existing.last_name)

    return Person(
        id=existing.id,
        family_id=existing.family_id,
        name=PersonName(first_name=first_name, last_name=last_name),
        gender=_resolve(command.gender, existing.gender),
        birth_date=_resolve(command.birth_date, existing.birth_date),
        death_date=_resolve(command.death_date, existing.death_date),
        birth_date_raw=_resolve(command.birth_date_raw, existing.birth_date_raw),
        death_date_raw=_resolve(command.death_date_raw, existing.death_date_raw),
    )


def _patch_affects_identity(command: PatchPersonCommand) -> bool:
    """Патч затрагивает поля, влияющие на уникальность в семье."""
    identity_fields = {"first_name", "last_name", "birth_date"}
    provided = {f for f in command.__dataclass_fields__ if not isinstance(getattr(command, f), UnsetType)}
    return bool(identity_fields & provided)
