"""
genealogy/application/uow.py

"""

from __future__ import annotations

from contextlib import suppress
from types import TracebackType

from shared.domain.exceptions import DatabaseError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from genealogy.domain.repositories.family import FamilyRepository
from genealogy.domain.repositories.graph import FamilyGraphRepository
from genealogy.domain.repositories.parent_child import ParentChildRepository
from genealogy.domain.repositories.person import PersonRepository
from genealogy.domain.repositories.sibling import SiblingRepository
from genealogy.domain.repositories.spouse import SpouseRepository


class GenealogyUoW:
    """
    Unit of Work для Genealogy контекста.
    """

    persons: PersonRepository
    families: FamilyRepository
    parent_child: ParentChildRepository
    spouses: SpouseRepository
    siblings: SiblingRepository
    family_graph: FamilyGraphRepository

    def __init__(
        self,
        session: AsyncSession,
        persons: PersonRepository,
        families: FamilyRepository,
        parent_child: ParentChildRepository,
        spouses: SpouseRepository,
        siblings: SiblingRepository,
        family_graph: FamilyGraphRepository,
    ) -> None:
        self._session = session
        self.persons = persons
        self.families = families
        self.parent_child = parent_child
        self.spouses = spouses
        self.siblings = siblings
        self.family_graph = family_graph

    async def __aenter__(self) -> GenealogyUoW:
        await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                with suppress(Exception):
                    await self._session.rollback()
        except DBAPIError as db_err:
            with suppress(Exception):
                await self._session.rollback()
            raise DatabaseError(detail=str(db_err)) from db_err
        finally:
            with suppress(Exception):
                await self._session.close()
