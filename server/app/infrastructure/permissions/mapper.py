from domain.entities.permission import PermissionEntity, RoleEntity
from infrastructure.db.models.permission import Permission, Role



def _map_permission(orm: Permission) -> PermissionEntity:
    return PermissionEntity(
        id=orm.id,
        codename=orm.codename,
        description=orm.description,
    )


def _map_role(orm: Role, permissions: list | None = None) -> RoleEntity:
    return RoleEntity(
        id=orm.id,
        name=orm.name,
        description=orm.description,
        permissions=permissions or [],
    )
