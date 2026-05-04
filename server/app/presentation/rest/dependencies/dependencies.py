"""
presentation/rest/dependencies/dependencies.py

Единственная точка входа для всех FastAPI-зависимостей.

Изменения:
  - get_current_account_id теперь проверяет Redis blacklist
  - Fail-open: если Redis недоступен — пропускаем blacklist проверку
  - extract_token читает из куки или Bearer заголовка (без изменений)
"""

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from genealogy.application.family.services import FamilyService
from genealogy.application.person.service import PersonService
from genealogy.application.relations.service import RelationService
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.application.permissions.service import PermissionService
from identity.infrastructure.auth.blacklist_service import is_blacklisted
from identity.infrastructure.auth.jwt_service import decode_access_token
from identity.infrastructure.uow_factory import IdentityUoWFactory
from shared.domain.exceptions import AuthenticationError
from shared.infrastructure.db.database import database


# ── UoW factories ─────────────────────────────────────────────────────────────


def get_identity_uow_factory() -> IdentityUoWFactory:
    return IdentityUoWFactory(database=database)


def get_genealogy_uow_factory() -> GenealogyUoWFactory:
    return GenealogyUoWFactory(database=database)


# ── Identity services ─────────────────────────────────────────────────────────


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


# ── Genealogy services ────────────────────────────────────────────────────────


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


# ── Auth helpers ──────────────────────────────────────────────────────────────

_bearer_optional = HTTPBearer(auto_error=False)


def extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """
    Извлекает raw JWT.

    Порядок:
      1. httpOnly-кука access_token  (браузерные клиенты)
      2. Authorization: Bearer        (Swagger UI / внешние API)
    """
    return request.cookies.get("access_token") or (credentials.credentials if credentials else None)


async def get_current_account_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> str:
    """
    Dependency: возвращает account_id из валидного, не отозванного access_token.

    Порядок проверок:
      1. Токен присутствует
      2. JWT подпись и TTL валидны
      3. jti не в Redis blacklist (fail-open при недоступности Redis)
      4. sub (account_id) присутствует в payload
    """
    token = extract_token(request, credentials)

    if not token:
        raise AuthenticationError(message="Not authenticated")

    payload = decode_access_token(token)

    # Blacklist-проверка (fail-open)
    jti: str | None = payload.get("jti")
    if jti and await is_blacklisted(jti):
        raise AuthenticationError(
            message="Токен отозван",
            errors={"token": "revoked"},
        )

    account_id: str | None = payload.get("sub")
    if not account_id:
        raise AuthenticationError(message="Invalid token payload")

    return account_id


async def get_current_token_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> dict:
    """
    Dependency: возвращает полный payload access token.
    Нужен в logout для извлечения jti и session_id.
    """
    token = extract_token(request, credentials)
    if not token:
        raise AuthenticationError(message="Not authenticated")
    return decode_access_token(token)
