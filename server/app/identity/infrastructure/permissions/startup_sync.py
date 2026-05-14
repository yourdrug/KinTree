"""
identity/infrastructure/permissions/startup_sync.py
"""

from __future__ import annotations

import logging

from shared.infrastructure.db.database import database

from identity.application.permissions.service import PermissionService
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger("default")


async def sync_permissions() -> None:
    """Синхронизирует пермишены и роли при старте."""
    uow_factory = IdentityUoWFactory(database=database)
    service = PermissionService(uow_factory=uow_factory)
    await service.sync_permissions()
