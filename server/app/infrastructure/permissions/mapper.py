from domain.entities.permission import PermissionEntity, RoleEntity, RolePermissionEntity

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


class RolePermissionMapper:
    @staticmethod
    def to_persistence(entity: RolePermissionEntity) -> dict:
        return {
            "id": entity.id,
            "role_id": entity.role_id,
            "permission_id": entity.permission_id,
        }


class RoleMapper:
    @staticmethod
    def to_persistence(entity: RoleEntity) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
        }


class PermissionMapper:
    @staticmethod
    def to_persistence(entity: PermissionEntity) -> dict:
        return {
            "id": entity.id,
            "codename": entity.codename,
            "description": entity.description,
        }
