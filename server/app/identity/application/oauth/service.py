"""
identity/application/oauth/service.py

OAuthService — application-сервис OAuth авторизации.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from shared.domain.exceptions import ConflictError, RoleDomainError
from shared.infrastructure.db.settings import settings

from identity.application.auth.commands import TokenPair
from identity.domain.entities.account import Account, create_account
from identity.domain.entities.account_role import create_account_role
from identity.domain.entities.oauth_account import OAuthAccount, OAuthProvider, create_oauth_account
from identity.domain.entities.permission import Role
from identity.domain.ports.oauth_provider import IOAuthProvider, OAuthUserInfo
from identity.domain.ports.token_service import ITokenService
from identity.domain.services.session_service import SessionDomainService
from identity.domain.value_objects.email import Email
from identity.infrastructure.uow_factory import IdentityUoWFactory


if TYPE_CHECKING:
    from identity.application.uow import IdentityUoW


logger = logging.getLogger(__name__)

# Домен синтетических email (Telegram и будущие провайдеры без email).
# Совпадает с _RESERVED_DOMAINS в Email VO.
_SYNTHETIC_EMAIL_DOMAINS = frozenset({"telegram.oauth", "oauth.internal"})


class OAuthService:
    """
    Application-сервис OAuth авторизации.

    Не знает о конкретных провайдерах — работает через IOAuthProvider.
    """

    def __init__(
        self,
        uow_factory: IdentityUoWFactory,
        token_service: ITokenService,
    ) -> None:
        self._uow_factory = uow_factory
        self._session_service = SessionDomainService(
            token_service=token_service,
            refresh_ttl_days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS,
        )

    async def handle_callback(
        self,
        provider: IOAuthProvider,
        raw_data: dict[str, Any],
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        """
        Единая точка входа для всех OAuth-провайдеров.

        Raises:
            ValueError: невалидные данные от провайдера.
            ConflictError: email уже зарегистрирован через пароль.
            AccountBlockedError: аккаунт заблокирован.
        """
        user_info = await provider.get_user_info(raw_data)
        oauth_provider = OAuthProvider(provider.provider_name)

        return await self._login_or_register(
            provider=oauth_provider,
            user_info=user_info,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    async def _login_or_register(
        self,
        provider: OAuthProvider,
        user_info: OAuthUserInfo,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenPair:
        async with self._uow_factory.create(master=True) as uow:
            oauth_account: OAuthAccount | None = await uow.oauth_accounts.get_by_provider(
                provider=provider,
                provider_user_id=user_info.provider_user_id,
            )

            if oauth_account is not None:
                account, role = await self._login(uow, oauth_account)
            else:
                account, role = await self._register(uow, provider, user_info)

            session = self._session_service.create_session(
                account=account,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            await uow.refresh_tokens.create(session.refresh_token)

        return TokenPair(
            access_token=session.access_token,
            refresh_token=session.raw_refresh_token,
            role=account.role_str,
            permissions=sorted(role.codenames),
        )

    async def _login(self, uow: IdentityUoW, oauth_account: OAuthAccount) -> tuple[Account, Role]:
        """Логин существующего OAuth-пользователя."""
        account = await uow.accounts.get_by_id(oauth_account.account_id)
        account.check_not_blocked()

        # Загружаем роль с пермишенами — нужна для TokenPair.permissions
        role = await uow.roles.get_by_name_with_permissions(name=account.role_name)
        if role is None:
            raise RoleDomainError(errors={"role": f"Роль {account.role_name} не найдена"})

        return account, role

    async def _register(
        self,
        uow: IdentityUoW,
        provider: OAuthProvider,
        user_info: OAuthUserInfo,
    ) -> tuple[Account, Role]:
        """Регистрация нового OAuth-пользователя."""
        email_str = user_info.email or ""

        # Проверяем конфликт только для реальных email (не синтетических)
        if not _is_synthetic_email(email_str):
            existing = await uow.accounts.get_by_email(email_str)
            if existing is not None:
                raise ConflictError(
                    message="Email уже зарегистрирован",
                    errors={"email": "Войдите по паролю или привяжите аккаунт."},
                )

        validated_email = Email.create(email_str)
        is_verified = user_info.is_email_verified and not _is_synthetic_email(email_str)

        account = create_account(
            email=validated_email,
            hashed_password=None,
            is_verified=is_verified,
        )

        role: Role | None = await uow.roles.get_by_name_with_permissions(name=account.role_name)
        if role is None:
            raise RoleDomainError(errors={"role": f"Роль {account.role_name} не найдена"})

        account_role = create_account_role(account_id=account.id, role_id=role.id)

        await uow.accounts.save(account=account)
        await uow.account_roles.assign_role(account_role=account_role)
        await uow.oauth_accounts.create(
            create_oauth_account(
                account_id=account.id,
                provider=provider,
                provider_user_id=user_info.provider_user_id,
            )
        )

        return account, role


def _is_synthetic_email(email: str) -> bool:
    """Синтетический email — от провайдера без реального email (Telegram)."""
    domain = email.split("@")[-1] if "@" in email else ""
    return domain in _SYNTHETIC_EMAIL_DOMAINS
