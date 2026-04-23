# genealogy/application/uow.py
from __future__ import annotations

from contextlib import suppress
from types import TracebackType

from genealogy.domain.repositories.parent_child import ParentChildRepository
from genealogy.domain.repositories.spouse import SpouseRepository
from shared.domain.exceptions import DatabaseError
from genealogy.domain.repositories.person import PersonRepository
from genealogy.domain.repositories.family import FamilyRepository

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession


class GenealogyUoW:
    """
    Unit of Work для Genealogy контекста.

    Содержит только репозитории, принадлежащие этому контексту.
    Не знает об Identity — никакого accounts/permissions здесь.
    """

    persons: PersonRepository
    families: FamilyRepository
    parent_child: ParentChildRepository
    spouses: SpouseRepository

    def __init__(
        self,
        session: AsyncSession,
        persons: PersonRepository,
        families: FamilyRepository,
        parent_child: ParentChildRepository,
        spouses: SpouseRepository,
    ) -> None:
        self._session = session
        self.persons = persons
        self.families = families
        self.parent_child = parent_child
        self.spouses = spouses

    async def __aenter__(self) -> GenealogyUoW:
        await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        with suppress(Exception):
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        with suppress(Exception):
            await self._session.close()

        if exc_type is not None and issubclass(exc_type, DBAPIError):
            raise DatabaseError(detail=str(exc_val)) from exc_val
