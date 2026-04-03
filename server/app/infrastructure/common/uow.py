"""
uow.py: File, containing common uow.
"""

from __future__ import annotations

from contextlib import suppress
from types import TracebackType

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.common.exceptions import DatabaseInteractionError


class UnitOfWork:
    def __init__(
        self,
        asession: AsyncSession,
        master: bool = False,
    ):
        """
        __init__: Initializes unit of work.

        Args:
            asession (AsyncSession): Asynchronous database session.
            master (bool): True if write operation, False if read operation.
        """

        self.asession: AsyncSession = asession
        self.master: bool = master

    async def __aenter__(
        self,
    ) -> UnitOfWork:
        """
        __aenter__: Enter method (context manager) for unit of work.

        Returns:
            UnitOfWork: Self.
        """

        await self.asession.begin()

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        __aexit__: Exit method (context manager) for unit of work.

        Args:
            exc_type ( Optional[type[BaseException]]): Type of exception that occur during cm.
            exc_val (Optional[BaseException]): Exception that occur during execution cm.
            exc_tb (Optional[TracebackType]): Traceback of exception that occur during execution cm.

        Raises:
            DatabaseInteractionError: Raised when connection error occurs.
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
