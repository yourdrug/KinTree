# domain/repositories/graph.py

from __future__ import annotations

from typing import Protocol

from domain.entities.parent_child import ParentChildRelation
from domain.entities.person import Person
from domain.entities.spouse import SpouseRelation


class FamilyGraphRepository(Protocol):
    """
    Репозиторий для построения графа семьи.
    Знает о связях между Person, ParentChild и Spouse — это его зона ответственности.
    Не заменяет PersonRepository/ParentChildRepository для обычных CRUD-операций.
    """

    async def get_persons_with_relations(
        self,
        family_id: str,
    ) -> tuple[list[Person], list[ParentChildRelation], list[SpouseRelation]]:
        """
        Три запроса в одном методе, один контекст сессии.
        Возвращает всё необходимое для построения графа.
        """
        ...
