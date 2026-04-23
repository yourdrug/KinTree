# api/dependencies/uow_factory.py
from fastapi import Depends
from genealogy.application.family.services import FamilyService
from genealogy.application.person.service import PersonService
from genealogy.application.relations.service import RelationService
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.application.permissions.service import PermissionService
from identity.infrastructure.uow_factory import IdentityUoWFactory
from shared.infrastructure.db.database import database


# ── Фабрики ──────────────────────────────────────────────────────────────────


def get_identity_uow_factory() -> IdentityUoWFactory:
    return IdentityUoWFactory(database=database)


def get_genealogy_uow_factory() -> GenealogyUoWFactory:
    return GenealogyUoWFactory(database=database)


# ── Identity Services ─────────────────────────────────────────────────────────


def get_auth_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
) -> AuthService:
    return AuthService(uow_factory=uow_factory)


def get_account_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
) -> AccountService:
    return AccountService(uow_factory=uow_factory)


def get_permission_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
) -> PermissionService:
    return PermissionService(uow_factory=uow_factory)


# ── Genealogy Services ────────────────────────────────────────────────────────


def get_person_service(
    uow_factory: GenealogyUoWFactory = Depends(get_genealogy_uow_factory),
) -> PersonService:
    return PersonService(uow_factory=uow_factory)


def get_family_service(
    uow_factory: GenealogyUoWFactory = Depends(get_genealogy_uow_factory),
) -> FamilyService:
    return FamilyService(uow_factory=uow_factory)


def get_relation_service(
    uow_factory: GenealogyUoWFactory = Depends(get_genealogy_uow_factory),
) -> RelationService:
    return RelationService(uow_factory=uow_factory)
