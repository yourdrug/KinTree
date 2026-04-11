from sqlalchemy import (
    Result,
    exists,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
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

    async def _check_exists(
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

    async def _get_count(
        self,
        statement: Select,
        distinct_column: InstrumentedAttribute | None = None,
    ) -> int:
        if distinct_column is not None:
            count_expr = func.count(func.distinct(distinct_column))
        else:
            count_expr = func.count()

        count_stmt: Select = select(count_expr).select_from(statement.subquery())
        result: Result = await self.session.execute(count_stmt)
        return result.scalar_one()
