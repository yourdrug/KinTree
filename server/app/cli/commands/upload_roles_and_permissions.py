"""
upload_roles_and_permissions.py

Функция загрузки ролей и разрешений.
"""

from __future__ import annotations

from logging import Logger, getLogger
import sys

from application.uow_factory import UoWFactory
from domain.entities.permission import (
    create_permission_entity,
    create_role_entity,
    create_role_permission_entity,
)
from domain.permissions.constants import role_permissions
from domain.permissions.enums import DefaultRole
from domain.permissions.enums import Permission as PermissionEnum


logger: Logger = getLogger("default")


async def upload_roles_and_permissions(uow_factory: UoWFactory) -> None:
    """
    Загружает роли и permissions в БД.

    Принципы:
    - одна транзакция (через UoW)
    - orchestration здесь
    """

    try:
        async with uow_factory.create(master=True) as uow:
            # --- 1. очистка ---
            await uow.roles.remove_all_permissions()
            await uow.roles.remove_all()
            await uow.permissions.remove_all()

            # --- 2. permissions ---
            permissions_map: dict[str, str] = {}

            for perm in PermissionEnum:
                entity = create_permission_entity(
                    codename=perm.value,
                    description=perm.description,
                )

                created = await uow.permissions.create(entity)
                permissions_map[perm.value] = created.id

            # --- 3. roles ---
            roles_map: dict[str, str] = {}

            for role in DefaultRole:
                role_entity = create_role_entity(
                    name=role.value,
                    description=role.description,
                )

                created = await uow.roles.create(role_entity)  # type: ignore
                roles_map[role.value] = created.id

            # --- 4. связи role ↔ permission ---
            for role, perms in role_permissions.items():
                role_id = roles_map[role.value]

                for perm in perms:
                    perm_id = permissions_map[perm.value]

                    relation = create_role_permission_entity(
                        role_id=role_id,
                        permission_id=perm_id,
                    )

                    await uow.roles.add_permission(relation)
    except Exception as exc:
        logger.error("Error while uploading roles and permissions", exc_info=exc)
        sys.exit(-1)
    else:
        logger.info("Roles and permissions successfully uploaded")
