from contextlib import suppress
from types import TracebackType
from typing import Generic, TypeVar

from domain.exceptions import DatabaseInteractionError
from sqlalchemy import (
    Result,
    exists,
    func,
    select,
)
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Select

from infrastructure.db.database import database
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


R = TypeVar("R", bound=BaseRepository)


class ManualRepositoryFactory(Generic[R]):
    """
    ManualRepositoryFactory: Context manager for manually creating a repository instance.
    """

    def __init__(
        self,
        repository_type: type[R],
        master: bool = False,
    ) -> None:
        """
        __init__: Initializes repository factory.

        Args:
            repository_type (type[R]): Repository class to instantiate.
            master (bool): True if write operation, False if read operation.
        """

        self.repository_type: type[R] = repository_type
        self.master: bool = master

    async def __aenter__(
        self,
    ) -> R:
        """
        __aenter__: Enter method (context manager) for repository factory.

        Returns:
            R: Repository.
        """

        self.asession: AsyncSession = database.get_session(master=self.master)

        await self.asession.begin()

        return self.repository_type(session=self.asession)

    async def __aexit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        """
        __aexit__: Exit method (context manager) for repository factory.

        Args:
            exc_type (type[BaseException]): Type of exception that occur during execution cm.
            exc_val (BaseException): Exception that occur during execution cm.
            exc_tb (TracebackType): Traceback of exception that occur during execution cm.
        """

        with suppress(Exception):
            if exc_type is None:
                await self.asession.commit()
            else:
                await self.asession.rollback()

        with suppress(Exception):
            await self.asession.close()

        if exc_type and issubclass(exc_type, DBAPIError):
            raise DatabaseInteractionError(
                message="Ошибка взаимодействия с БД",
                errors={"details": f"{exc_val}"},
            )
        return None
