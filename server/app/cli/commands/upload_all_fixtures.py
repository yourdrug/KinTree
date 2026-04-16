"""
upload_all_fixtures.py: File, containing command for uploading all fixtures.
"""

from logging import (
    Logger,
    getLogger,
)
import sys

from cli.commands.upload_account_permissions import upload_account_permissions
from cli.commands.upload_account_roles import upload_account_roles
from cli.commands.upload_account_roles_account_permissions import upload_account_roles_account_permissions


logger: Logger = getLogger("default")


async def upload_all_fixtures(profile: str = "development") -> None:
    """
    upload_all_fixtures: Command for uploading all fixtures.

    Args:
        profile (str): Profile name
    """

    try:
        await upload_account_roles(profile)
        await upload_account_permissions(profile)
        await upload_account_roles_account_permissions(profile)
    except Exception as exception:
        logger.error("Error while uploading all fixtures", exc_info=exception)
        sys.exit(-1)
    else:
        logger.info("All fixtures uploaded")
