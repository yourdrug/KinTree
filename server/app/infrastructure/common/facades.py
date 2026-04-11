from domain.repositories.account import AbstractAccountRepository
from domain.repositories.family import AbstractFamilyRepository
from domain.repositories.person import AbstractPersonRepository
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.account.repositories import AccountRepository
from infrastructure.family.repositories import FamilyRepository
from infrastructure.person.repositories import PersonRepository


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

        self.account_repository: AbstractAccountRepository = AccountRepository(asession)

        self.person_repository: AbstractPersonRepository = PersonRepository(asession)

        self.family_repository: AbstractFamilyRepository = FamilyRepository(asession)
