# presentation/rest/dependencies/dependencies.py
#
# Единственная точка входа для всех FastAPI-зависимостей.
# Роутеры любого bounded context импортируют зависимости ТОЛЬКО отсюда —
# никаких прямых импортов из чужого контекста в роутерах.
#
# Composition root: здесь разрешено смешивать identity и genealogy.

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from genealogy.application.family.services import FamilyService
from genealogy.application.person.service import PersonService
from genealogy.application.relations.service import RelationService
from genealogy.infrastructure.uow_factory import GenealogyUoWFactory
from identity.application.account.service import AccountService
from identity.application.auth.service import AuthService
from identity.application.permissions.service import PermissionService
from identity.infrastructure.auth.jwt_service import decode_access_token
from identity.infrastructure.uow_factory import IdentityUoWFactory
from shared.domain.exceptions import AuthenticationError
from shared.infrastructure.db.database import database


# ── Фабрики UoW ──────────────────────────────────────────────────────────────


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


# ── Auth helpers ──────────────────────────────────────────────────────────────
#
# HTTPBearer с auto_error=False — не бросает 403 при отсутствии заголовка,
# позволяя нашему коду кидать AuthenticationError с единым форматом ошибок.

_bearer_optional = HTTPBearer(auto_error=False)


def extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """
    Извлекает raw JWT.

    Порядок приоритета:
      1. httpOnly-кука ``access_token``  (браузерные клиенты)
      2. Authorization: Bearer <token>   (Swagger UI / API-клиенты)

    Возвращает None если токен не найден ни там, ни там.
    """
    return request.cookies.get("access_token") or (
        credentials.credentials if credentials else None
    )


async def get_current_account_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> str:
    """
    Dependency: возвращает account_id из валидного access_token.

    Используется как в identity-роутах, так и в cookie-роутах —
    через единую точку разрешения токена.

    Бросает AuthenticationError если токен отсутствует или невалиден.
    """
    token = extract_token(request, credentials)

    if not token:
        raise AuthenticationError(message="Not authenticated")

    payload = decode_access_token(token)  # бросает AuthenticationError при невалидном токене
    account_id: str | None = payload.get("sub")

    if not account_id:
        raise AuthenticationError(message="Invalid token payload")

    return account_id
