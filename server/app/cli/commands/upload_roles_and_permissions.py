"""
upload_roles_and_permissions.py: File, containing command for uploading acc roles-perms.
"""

from logging import (
    Logger,
    getLogger,
)
import sys

from domain.entities.permission import (
    create_permission_entity,
    create_role_entity,
    create_role_permission_entity,
)
from domain.permissions.constants import role_permissions
from domain.permissions.enums import DefaultRole
from domain.permissions.enums import Permission as PermissionEnum
from infrastructure.common.repositories import ManualRepositoryFactory
from infrastructure.permissions.repositories import PermissionRepository, RoleRepository


logger: Logger = getLogger("default")


async def upload_roles_and_permissions() -> None:
    """
    upload_account_roles_account_permissions: Command for uploading account roles and permissions.
    Read fixtures from json file and upsert them.
    """

    try:
        permissions_map: dict[str, str] = {}

        async with ManualRepositoryFactory(PermissionRepository, master=True) as repository:
            await repository.delete_all_permissions()

            for perm in PermissionEnum:
                permission_entity = create_permission_entity(
                    codename=perm.value,
                    description=perm.description,
                )
                await repository.create_permission(permission=permission_entity)
                permissions_map[perm.value] = permission_entity.id

        async with ManualRepositoryFactory(RoleRepository, master=True) as repository:
            await repository.delete_all_role_permission()
            await repository.delete_all_roles()

            roles_map: dict[str, str] = {}

            for role in DefaultRole:
                role_entity = create_role_entity(
                    name=role.value,
                    description=role.description,
                )
                await repository.create_role(role_entity=role_entity)
                roles_map[role.value] = role_entity.id

            for role, perms in role_permissions.items():
                role_id = roles_map[role.value]

                for perm in perms:
                    perm_id = permissions_map[perm.value]

                    role_permission_entity = create_role_permission_entity(
                        role_id=role_id,
                        permission_id=perm_id,
                    )
                    await repository.create_role_permissions(role_permission=role_permission_entity)
    except Exception as exception:
        logger.error("Error while uploading account roles and permissions", exc_info=exception)
        sys.exit(-1)
    else:
        logger.info("Role permissions uploaded")
