"""
upload_permissions.py: File, containing command for uploading account permissions.
"""

from json import loads
from logging import (
    Logger,
    getLogger,
)
import sys

from domain.entities.permission import PermissionEntity
from infrastructure.common.repositories import ManualRepositoryFactory
from infrastructure.permissions.repositories import PermissionRepository


logger: Logger = getLogger("default")


async def upload_account_permissions(profile: str = "development") -> None:
    """
    upload_account_permissions: Command for uploading account permissions.
    Read fixtures from json file and upsert them.

    Args:
        profile (str): Profile name
    """

    try:
        with open(f"cli/fixtures/{profile}/account_permissions.json") as file:
            account_permissions: list = loads(file.read())

        async with ManualRepositoryFactory(PermissionRepository, master=True) as repository:
            for account_permission in account_permissions:
                permission_entity = PermissionEntity(
                    id=account_permission["id"],
                    codename=account_permission["codename"],
                    description=account_permission["description"],
                )
                await repository.create_permission(permission_entity)
    except Exception as exception:
        logger.error("Error while uploading account permissions", exc_info=exception)
        sys.exit(-1)
    else:
        logger.info("Account permissions uploaded")
