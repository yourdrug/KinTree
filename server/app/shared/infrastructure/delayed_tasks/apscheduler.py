"""
shared/infrastructure/delayed_tasks/apscheduler.py

File, containing scheduler.
"""

from logging import (
    Logger,
    getLogger,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from identity.infrastructure.jobs import (
    cleanup_expired_email_tokens,
    cleanup_expired_refresh_tokens,
)

from shared.infrastructure.db.settings import settings


logger: Logger = getLogger("default")


class Scheduler:
    """
    Scheduler: Asyncio scheduler.
    """

    def __init__(
        self,
    ) -> None:
        """
        __init__: Initializes scheduler.
        """

        self.scheduler: AsyncIOScheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

    async def _configure(
        self,
    ) -> None:
        """
        _configure: Configures scheduler.
        """

        self.scheduler.add_job(
            id=f"{cleanup_expired_email_tokens.__name__}",
            func=cleanup_expired_email_tokens,
            replace_existing=True,
            trigger="interval",
            max_instances=1,
            minutes=6 * 60,
        )

        self.scheduler.add_job(
            id=f"{cleanup_expired_refresh_tokens.__name__}",
            func=cleanup_expired_refresh_tokens,
            replace_existing=True,
            trigger="interval",
            max_instances=1,
            minutes=6 * 60,
        )

    async def _cleanup(
        self,
    ) -> None:
        """
        _cleanup: Cleans up scheduler.
        """

        self.scheduler.remove_all_jobs()

    async def startup(
        self,
    ) -> None:
        """
        startup: Starts scheduler.
        """

        await self._configure()
        self.scheduler.start()
        logger.info("Scheduler started.")

    async def shutdown(
        self,
    ) -> None:
        """
        shutdown: Shuts down scheduler.
        """

        await self._cleanup()
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped.")


scheduler: Scheduler = Scheduler()
