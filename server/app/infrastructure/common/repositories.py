from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import (
    exists,
    func,
    select,
)
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from infrastructure.db.models.basemodel import BaseModel


class BaseRepository:
    """
    BaseRepository: Abstract base repository providing common database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        """
        __init__: Initializes the repository with a database session.

        Args:
            session (AsyncSession): SQLAlchemy async session instance.
        """

        self.session: AsyncSession = session

    async def check_object_exists(
        self,
        object_id: str,
        model: type[BaseModel],
    ) -> bool:
        """
        check_object_exists: Generic method to check object existence.

        Args:
            object_id: ID of the object to check.
            model: SQLAlchemy model class.

        Returns:
            True if object exists, False otherwise.
        """

        statement: Select = select(exists().where(model.id == object_id))
        result = await self.session.execute(statement)

        return result.scalar() or False

    async def get_object_count(
        self,
        model: type[BaseModel],
        filter: Filter | None,
        authenticated_account: dict | None,
        distinct: bool = False,
    ) -> int:
        """
        get_object_count: Generic method to get object count.

        Args:
            model (type[BaseModel]): SQLAlchemy model class.
            filter (Optional[Filter]): SQLAlchemy filter.
            scope (Optional[ScopeName]): Scope of the object.
            authenticated_account (Optional[dict]): Authenticated account data.

        Returns:
            int: Number of entities.
        """

        statement: Select

        if distinct:
            statement = select(func.count(func.distinct(model.id))).select_from(model)
        else:
            statement = select(func.count(model.id)).select_from(model)

        statement = await self._apply_filter(statement, filter)

        result: Result = await self.session.execute(statement)
        total: int = result.scalar_one()

        return total

    async def _apply_filter(
        self,
        statement: Select,
        filter: Filter | None,
    ) -> Select:
        """
        _apply_filter: Abstract method for applying filter to the statement.
        """

        raise NotImplementedError

    async def _apply_sort(
        self,
        statement: Select,
        filter: Filter | None,
    ) -> Select:
        """
        _apply_sort: Abstract method for applying sort to the statement.
        """

        raise NotImplementedError
