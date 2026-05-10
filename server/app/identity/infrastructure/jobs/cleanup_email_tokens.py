"""
identity/infrastructure/jobs/cleanup_email_tokens.py

Фоновая задача очистки истёкших email-токенов.
"""

from __future__ import annotations

import logging

from shared.infrastructure.db.database import database

from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


async def cleanup_expired_email_tokens() -> None:
    """Удаляет истёкшие записи из email_tokens."""
    uow_factory: IdentityUoWFactory = IdentityUoWFactory(database=database)

    async with uow_factory.create(master=True) as uow:
        deleted = await uow.email_tokens.delete_expired()

    if deleted:
        logger.info("Cleaned up %d expired email tokens", deleted)
