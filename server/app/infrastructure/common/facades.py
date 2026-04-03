from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.accounts.repositories import AccountRepository


class BaseFacade:
    """
    BaseFacade: Base class for all facades.
    """

    pass


class RepositoryFacade(BaseFacade):
    """
    RepositoryFacade: Facade for repositories.
    """

    def __init__(
        self,
        asession: AsyncSession,
    ) -> None:
        """
        __init__: Initializes the repository facade.

        Args:
            asession (AsyncSession): Asynchronous database session.
        """

        self.account_repository: AccountRepository = AccountRepository(asession)
