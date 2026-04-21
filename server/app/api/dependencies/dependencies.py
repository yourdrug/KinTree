# ── Database ──────────────────────────────────────────────────────────────────
from application.account.service import AccountService
from application.auth.service import AuthService
from application.family.services import FamilyService
from application.permissions.service import PermissionService
from application.person.service import PersonService
from application.relations.service import RelationService
from fastapi import Depends
from infrastructure.db.database import database
from infrastructure.uow_factory import UoWFactory


def get_uow_factory() -> UoWFactory:
    """Создаёт UoWFactory, подключённый к текущему DatabaseManager."""
    return UoWFactory(database=database)


# ── Services ──────────────────────────────────────────────────────────────────


def get_person_service(
    uow_factory: UoWFactory = Depends(get_uow_factory),
) -> PersonService:
    return PersonService(uow_factory=uow_factory)


def get_family_service(
    uow_factory: UoWFactory = Depends(get_uow_factory),
) -> FamilyService:
    return FamilyService(uow_factory=uow_factory)


def get_account_service(
    uow_factory: UoWFactory = Depends(get_uow_factory),
) -> AccountService:
    return AccountService(uow_factory=uow_factory)


def get_auth_service(
    uow_factory: UoWFactory = Depends(get_uow_factory),
) -> AuthService:
    return AuthService(uow_factory=uow_factory)


def get_relation_service(
    uow_factory: UoWFactory = Depends(get_uow_factory),
) -> RelationService:
    return RelationService(uow_factory=uow_factory)


def get_permission_service(
    uow_factory: UoWFactory = Depends(get_uow_factory),
) -> PermissionService:
    return PermissionService(uow_factory=uow_factory)
