from domain.entities.permission import AccountRoleEntity, PermissionEntity, RoleEntity, RolePermissionEntity

from infrastructure.db.models.permission import AccountRole, Permission, Role


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
    def to_domain(orm: Role, permissions: list[PermissionEntity] | None = None) -> RoleEntity:
        return RoleEntity(
            id=orm.id,
            name=orm.name,
            description=orm.description,
            permissions=permissions or [],
        )

    @staticmethod
    def to_persistence(entity: RoleEntity) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
        }


class PermissionMapper:
    @staticmethod
    def to_domain(orm: Permission) -> PermissionEntity:
        return PermissionEntity(
            id=orm.id,
            codename=orm.codename,
            description=orm.description,
        )

    @staticmethod
    def to_persistence(entity: PermissionEntity) -> dict:
        return {
            "id": entity.id,
            "codename": entity.codename,
            "description": entity.description,
        }


class AccountRoleMapper:
    @staticmethod
    def to_domain(orm: AccountRole) -> AccountRoleEntity:
        return AccountRoleEntity(
            id=orm.id,
            account_id=orm.account_id,
            role_id=orm.role_id,
        )

    @staticmethod
    def to_persistence(entity: AccountRoleEntity) -> dict:
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "role_id": entity.role_id,
        }
