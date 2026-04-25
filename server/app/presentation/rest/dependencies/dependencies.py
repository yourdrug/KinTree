# presentation/rest/dependencies/dependencies.py
#
# Единственная точка входа для всех FastAPI-зависимостей.
# Роутеры любого bounded context импортируют зависимости ТОЛЬКО отсюда —
# никаких прямых импортов из чужого контекста в роутерах.
#
# Composition root: здесь разрешено смешивать identity и genealogy.

from fastapi import Depends
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


# ── Auth Helpers ────────────────────────────────────────────────────────

# auto_error=False lets us raise a custom AuthenticationError instead of
# FastAPI's generic 403, which keeps our error format consistent.
_bearer = HTTPBearer(auto_error=False)


async def get_current_account_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    Декодирует Bearer-токен и возвращает account_id.
    Бросает AuthenticationError если токен отсутствует или невалиден.
    """
    if credentials is None:
        raise AuthenticationError(
            message="Требуется авторизация",
            errors={"Authorization": "Заголовок отсутствует"},
        )

    payload = decode_access_token(credentials.credentials)
    account_id: str | None = payload.get("sub")

    if not account_id:
        raise AuthenticationError(
            message="Недействительный токен",
            errors={"sub": "Отсутствует идентификатор аккаунта"},
        )

    return account_id
