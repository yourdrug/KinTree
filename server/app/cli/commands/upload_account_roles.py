"""
upload_roles.py: File, containing command for uploading account roles.
"""

from json import loads
from logging import (
    Logger,
    getLogger,
)
import sys

from domain.entities.permission import RoleEntity
from infrastructure.common.repositories import ManualRepositoryFactory
from infrastructure.permissions.repositories import RoleRepository


logger: Logger = getLogger("default")


async def upload_account_roles(profile: str = "development") -> None:
    """
    upload_account_roles: Command for uploading account roles.
    Read fixtures from json file and upsert them.

    Args:
        profile (str): Profile name
    """

    try:
        with open(f"cli/fixtures/{profile}/account_roles.json") as file:
            account_roles: list = loads(file.read())

        async with ManualRepositoryFactory(RoleRepository, master=True) as repository:
            for account_role in account_roles:
                role_entity = RoleEntity(
                    id=account_role["id"],
                    name=account_role["name"],
                    description=account_role["description"],
                )
                await repository.create_role(role_entity)
    except Exception as exception:
        logger.error("Error while uploading account roles", exc_info=exception)
        sys.exit(-1)
    else:
        logger.info("Account roles uploaded")
