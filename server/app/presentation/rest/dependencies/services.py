"""
presentation/rest/dependencies/services.py

Единственная точка DI для FastAPI.
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPBearer
from genealogy.application.family.services import FamilyService
from genealogy.application.person.service import PersonService
from genealogy.application.relations.service import RelationService
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.application.oauth.service import OAuthService
from identity.application.permissions.service import PermissionService
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.ports.token_service import ITokenService
from identity.infrastructure.auth.password_hasher import get_password_hasher
from identity.infrastructure.auth.token_service import get_token_service
from identity.infrastructure.uow_factory import IdentityUoWFactory
from shared.infrastructure.db.database import database


bearer = HTTPBearer(auto_error=False)


def get_identity_uow_factory() -> IdentityUoWFactory:
    return IdentityUoWFactory(database=database)


def get_genealogy_uow_factory() -> GenealogyUoWFactory:
    return GenealogyUoWFactory(database=database)


# ── Adapters ───────────────────────────────────────────────────────────────────


def get_password_hasher_dep() -> IPasswordHasher:
    return get_password_hasher()


def get_token_service_dep() -> ITokenService:
    return get_token_service()


# ── Identity services ──────────────────────────────────────────────────────────


def get_auth_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
    password_hasher: IPasswordHasher = Depends(get_password_hasher_dep),
    token_service: ITokenService = Depends(get_token_service_dep),
) -> AuthService:
    return AuthService(
        uow_factory=uow_factory,
        password_hasher=password_hasher,
        token_service=token_service,
    )


def get_oauth_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
    token_service: ITokenService = Depends(get_token_service_dep),
) -> OAuthService:
    return OAuthService(
        uow_factory=uow_factory,
        token_service=token_service,
    )


def get_account_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
) -> AccountService:
    return AccountService(uow_factory=uow_factory)


def get_permission_service(
    uow_factory: IdentityUoWFactory = Depends(get_identity_uow_factory),
) -> PermissionService:
    return PermissionService(uow_factory=uow_factory)


# ── Genealogy services ─────────────────────────────────────────────────────────


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
