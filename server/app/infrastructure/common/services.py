from infrastructure.common.facades import RepositoryFacade
from infrastructure.common.uow import UnitOfWork


class BaseService:
    """
    BaseService: Abstract base service providing common functionality.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        repository_facade: RepositoryFacade,
    ) -> None:
        """
        __init__: Initializes the service with a Unit of Work instance.

        Args:
            uow (UnitOfWork): Unit of Work for database transaction management.
            repository_facade (RepositoryFacade): Facade for repository access.
        """

        self.uow: UnitOfWork = uow
        self.repository_facade: RepositoryFacade = repository_facade
