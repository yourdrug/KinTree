from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from genealogy.infrastructure.relations.parent_child_repository import ParentChildRepositoryImpl
from genealogy.infrastructure.relations.spouse_repository import SpouseRepositoryImpl
from shared.infrastructure.db.database import DatabaseManager
from genealogy.application.uow import GenealogyUoW
from genealogy.infrastructure.person.repositories import PersonRepositoryImpl
from genealogy.infrastructure.family.repositories import FamilyRepositoryImpl


class GenealogyUoWFactory:
    def __init__(self, database: DatabaseManager) -> None:
        self._database = database

    @asynccontextmanager
    async def create(self, master: bool = False) -> AsyncGenerator[GenealogyUoW, None]:
        session = self._database.get_session(master=master)
        uow = GenealogyUoW(
            session=session,
            persons=PersonRepositoryImpl(session=session),
            families=FamilyRepositoryImpl(session=session),
            parent_child=ParentChildRepositoryImpl(session=session),
            spouses=SpouseRepositoryImpl(session=session),
        )

        async with uow:
            yield uow
