"""
upload_account_roles_account_permissions.py: File, containing command for uploading acc roles-perms.
"""


import sys
from json import loads
from logging import (
    Logger,
    getLogger,
)

from common.dependencies import ManualRepositoryFactory
from common.utils import parse_json
from roles.repositories import AccountRoleAccountPermissionRepository


logger: Logger = getLogger('default')


async def upload_account_roles_account_permissions(profile: str = 'development') -> None:
    """
    upload_account_roles_account_permissions: Command for uploading account roles and permissions.
    Read fixtures from json file and upsert them.

    Args:
        profile (str): Profile name
    """

    try:
        with open(f'cli/fixtures/{profile}/account_roles_account_permissions.json') as file:
            account_roles_account_permissions: list = loads(file.read())

        async with ManualRepositoryFactory(
            AccountRoleAccountPermissionRepository,
            master=True,
        ) as repository:
            await repository.delete_all_role_pemission()

            for account_role_account_permission in account_roles_account_permissions:
                await repository.insert_or_update(account_role_account_permission)
    except Exception as exception:
        logger.error('Error while uploading account roles and permissions', exc_info=exception)
        sys.exit(-1)
    else:
        logger.info('AccountRoleAccountPermissionRepository uploaded')
