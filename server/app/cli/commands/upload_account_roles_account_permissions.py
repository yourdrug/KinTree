"""
upload_account_roles_account_permissions.py: File, containing command for uploading acc roles-perms.
"""

from json import loads
from logging import (
    Logger,
    getLogger,
)
import sys

from domain.entities.permission import RolePermissionEntity
from infrastructure.common.repositories import ManualRepositoryFactory
from infrastructure.permissions.repositories import RoleRepository


logger: Logger = getLogger("default")


async def upload_account_roles_account_permissions(profile: str = "development") -> None:
    """
    upload_account_roles_account_permissions: Command for uploading account roles and permissions.
    Read fixtures from json file and upsert them.

    Args:
        profile (str): Profile name
    """

    try:
        with open(f"cli/fixtures/{profile}/account_roles_account_permissions.json") as file:
            account_roles_account_permissions: list = loads(file.read())

        async with ManualRepositoryFactory(RoleRepository, master=True) as repository:
            await repository.delete_all_role_permission()

            for account_role_account_permission in account_roles_account_permissions:
                role_permission_entity = RolePermissionEntity(
                    id=account_role_account_permission["id"],
                    role_id=account_role_account_permission["role_id"],
                    permission_id=account_role_account_permission["permission_id"],
                )
                await repository.insert_or_update(role_permission_entity)
    except Exception as exception:
        logger.error("Error while uploading account roles and permissions", exc_info=exception)
        sys.exit(-1)
    else:
        logger.info("Role permissions uploaded")
