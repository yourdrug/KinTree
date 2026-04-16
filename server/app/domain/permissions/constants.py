# Дефолтные разрешения для каждой роли
from domain.permissions.enums import DefaultRole, Permission as PermissionEnum


role_permissions: dict[str, list[str]] = {
    DefaultRole.GUEST: [
        PermissionEnum.FAMILY__READ,
        PermissionEnum.PERSON__READ,
    ],
    DefaultRole.USER: [
        PermissionEnum.FAMILY__READ,
        PermissionEnum.FAMILY__CREATE,
        PermissionEnum.FAMILY__UPDATE_OWN,
        PermissionEnum.FAMILY__DELETE_OWN,
        PermissionEnum.PERSON__READ,
        PermissionEnum.PERSON__CREATE,
        PermissionEnum.PERSON__UPDATE_OWN,
        PermissionEnum.PERSON__DELETE_OWN,
        PermissionEnum.ACCOUNT__READ_SELF,
    ],
    DefaultRole.MODERATOR: [
        PermissionEnum.FAMILY__READ,
        PermissionEnum.FAMILY__CREATE,
        PermissionEnum.FAMILY__UPDATE_OWN,
        PermissionEnum.FAMILY__DELETE_OWN,
        PermissionEnum.FAMILY__UPDATE_ANY,
        PermissionEnum.PERSON__READ,
        PermissionEnum.PERSON__CREATE,
        PermissionEnum.PERSON__UPDATE_OWN,
        PermissionEnum.PERSON__DELETE_OWN,
        PermissionEnum.PERSON__UPDATE_ANY,
        PermissionEnum.PERSON__DELETE_ANY,
        PermissionEnum.ACCOUNT__READ_SELF,
        PermissionEnum.ACCOUNT__READ_ANY,
    ],
    DefaultRole.ADMIN: [p.value for p in PermissionEnum],  # все разрешения
}
