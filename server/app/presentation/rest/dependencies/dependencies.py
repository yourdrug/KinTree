"""
presentation/rest/dependencies/dependencies.py

Единственная точка DI для FastAPI.

Регистрирует адаптеры под порты:
  IPasswordHasher → BcryptPasswordHasher
  ITokenService   → JWTTokenService

AuthService получает зависимости через конструктор — не импортирует infrastructure.
FastAPI dependencies — тонкая обёртка, которая связывает порты с адаптерами.
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from genealogy.application.family.services import FamilyService
from genealogy.application.person.service import PersonService
from genealogy.application.relations.service import RelationService
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.application.permissions.service import PermissionService
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.ports.token_service import AccessTokenPayload, ITokenService
from identity.infrastructure.auth.blacklist_service import is_blacklisted
from identity.infrastructure.auth.password_hasher import get_password_hasher
from identity.infrastructure.auth.token_service import get_token_service
from identity.infrastructure.uow_factory import IdentityUoWFactory
from shared.domain.exceptions import AuthenticationError
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


# ── Auth helpers ───────────────────────────────────────────────────────────────


def extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Cookie → Bearer. Cookie приоритетнее (браузерные клиенты)."""
    return request.cookies.get("access_token") or (credentials.credentials if credentials else None)


async def get_current_account_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    token_service: ITokenService = Depends(get_token_service_dep),
) -> str:
    """
    Dependency: account_id из валидного, не отозванного access_token.

    Проверки:
      1. Токен присутствует
      2. Подпись и TTL валидны (decode_access_token)
      3. jti не в Redis blacklist (fail-open при недоступности Redis)
    """
    token = extract_token(request, credentials)
    if not token:
        raise AuthenticationError(message="Not authenticated")

    payload: AccessTokenPayload = token_service.decode_access_token(token)

    if payload.jti and await is_blacklisted(payload.jti):
        raise AuthenticationError(
            message="Токен отозван",
            errors={"token": "revoked"},
        )

    return payload.account_id


async def get_current_token_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    token_service: ITokenService = Depends(get_token_service_dep),
) -> AccessTokenPayload:
    """
    Dependency: полный payload access token как typed VO.
    Нужен в logout для извлечения jti и session_id.
    """
    token = extract_token(request, credentials)
    if not token:
        raise AuthenticationError(message="Not authenticated")
    return token_service.decode_access_token(token)
