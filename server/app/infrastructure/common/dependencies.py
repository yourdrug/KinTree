from collections.abc import AsyncGenerator, Callable
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.common.database import database
from infrastructure.common.facades import RepositoryFacade
from infrastructure.common.services import BaseService
from infrastructure.common.uow import UnitOfWork


@lru_cache
def get_asession(
    master: bool = False,
) -> Callable[..., AsyncGenerator[AsyncSession, None]]:
    """
    get_asession: Decorator for creating async database session dependency providers.
    """

    async def wrapper() -> AsyncGenerator[AsyncSession, None]:
        """
        wrapper: Dependency provider for AsyncSession instance.
        Creates and manages the lifecycle of an async database session.
        ITS FOR FastAPI Depends.

        Args:
            master (bool): True if write operation, False if read operation.

        Yields:
            AsyncGenerator[AsyncSession, None]: Generator yielding an AsyncSession instance.
        """

        asession: AsyncSession = database.get_session(master=master)

        try:
            yield asession
        finally:
            await asession.close()

    return wrapper


def get_uow(master: bool = False) -> Callable[..., AsyncGenerator[UnitOfWork, None]]:
    """
    get_uow: Decorator for creating UnitOfWork dependency providers.
    """

    async def wrapper(
        asession: AsyncSession = Depends(get_asession(master=master), use_cache=True),
    ) -> AsyncGenerator[UnitOfWork, None]:
        """
        wrapper: Dependency provider for UnitOfWork instance.
        ITS FOR FastAPI Depends.

        Args:
            asession (AsyncSession): Injected database session dependency from get_asession.

        Yields:
            AsyncGenerator[UnitOfWork, None]: Generator yielding a UnitOfWork instance.
        """

        yield UnitOfWork(asession=asession, master=master)

    return wrapper


def get_repository_facade(
    master: bool = False,
) -> Callable[..., AsyncGenerator[RepositoryFacade, None]]:
    """
    get_repository_facade: Decorator for creating RepositoryFacade dependency providers.
    """

    async def wrapper(
        asession: AsyncSession = Depends(get_asession(master=master), use_cache=True),
    ) -> AsyncGenerator[RepositoryFacade, None]:
        """
        wrapper: Dependency provider for RepositoryFacade instance.
        ITS FOR FastAPI Depends.

        Args:
            asession (AsyncSession): Injected database session dependency from get_asession.

        Yields:
            AsyncGenerator[RepositoryFacade, None]: Generator yielding a RepositoryFacade instance.
        """

        yield RepositoryFacade(asession=asession)

    return wrapper


def get_service(
    service_type: type[BaseService],
    master: bool = False,
) -> Callable[..., AsyncGenerator[BaseService, None]]:
    """
    get_service: Factory for creating service dependency providers.
    ITS FOR FastAPI Depends.

    Args:
        service_type (type[BaseService]): Service class to instantiate.
        master (bool): True if write operation, False if read operation.

    Returns:
        Callable[..., AsyncGenerator[BaseService, None]]: Dependency provider function.
    """

    async def wrapper(
        uow: UnitOfWork = Depends(get_uow(master=master)),
        repository_facade: RepositoryFacade = Depends(get_repository_facade(master=master)),
    ) -> AsyncGenerator[BaseService, None]:
        """
        wrapper: Inner dependency provider for specific service type.

        Args:
            uow (UnitOfWork): Injected UnitOfWork dependency.
            repository_facade (RepositoryFacade): Injected RepositoryFacade dependency.

        Yields:
            AsyncGenerator[BaseService, None]: Generator yielding a service instance.
        """

        yield service_type(
            uow=uow,
            repository_facade=repository_facade,
        )

    return wrapper
