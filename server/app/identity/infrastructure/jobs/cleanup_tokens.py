"""
identity/infrastructure/jobs/cleanup_tokens.py

Фоновая задача для очистки истёкших refresh_tokens.

Запуск: добавить в планировщик (APScheduler, Celery Beat, или простой asyncio.create_task).

Пример запуска каждые 6 часов через APScheduler:

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from identity.infrastructure.jobs.cleanup_tokens import cleanup_expired_refresh_tokens

    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleanup_expired_refresh_tokens, "interval", hours=6)
    scheduler.start()

Или через lifespan в main.py:

    import asyncio

    async def _cleanup_loop():
        while True:
            await asyncio.sleep(6 * 3600)
            await cleanup_expired_refresh_tokens()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(_cleanup_loop())
"""

from __future__ import annotations

import logging

from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


async def cleanup_expired_refresh_tokens(uow_factory: IdentityUoWFactory) -> None:
    """Удаляет истёкшие записи из refresh_tokens."""
    async with uow_factory.create() as uow:
        deleted = await uow.refresh_tokens.delete_expired()

    if deleted:
        logger.info("Cleaned up %d expired refresh tokens", deleted)
