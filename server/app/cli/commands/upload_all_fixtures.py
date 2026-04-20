"""
upload_all_fixtures.py: File, containing command for uploading all fixtures.
"""

from logging import Logger, getLogger
import sys

from application.uow_factory import UoWFactory

from cli.commands.upload_roles_and_permissions import upload_roles_and_permissions


logger: Logger = getLogger("default")


async def upload_all_fixtures(uow_factory: UoWFactory, profile: str = "development") -> None:
    """
    upload_all_fixtures: Command for uploading all fixtures.

    Args:
        uow_factory: unit of work factory
        profile (str): Profile name
    """

    try:
        await upload_roles_and_permissions(uow_factory)
    except Exception as exception:
        logger.error("Error while uploading all fixtures", exc_info=exception)
        sys.exit(-1)
    else:
        logger.info("All fixtures uploaded")
