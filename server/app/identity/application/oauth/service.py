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


class OAuthService:
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

        async with self._uow_factory.create(master=True) as uow:
            oauth_account: OAuthAccount | None = await uow.oauth_accounts.get_by_provider(
                provider=oauth_provider,
                provider_user_id=user_info.provider_user_id,
            )

            if oauth_account is not None:
                account, role = await self._login(uow, oauth_account)
            else:
                account, role = await self._register(uow, oauth_provider, user_info)

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
        # Провайдер уже построил правильный email через Email.create_synthetic или обычный.
        # OAuthUserInfo.email — всегда строка (провайдер гарантирует).
        # Восстанавливаем VO из строки через правильную фабрику на основе is_synthetic().
        raw_email = user_info.email or ""
        email = Email.from_provider(raw_email)

        # Проверка конфликта только для реальных email — логика в VO
        if not email.is_synthetic():
            existing = await uow.accounts.get_by_email(email.value)
            if existing is not None:
                raise ConflictError(
                    message="Email уже зарегистрирован",
                    errors={"email": "Войдите по паролю или привяжите аккаунт."},
                )

        account = create_account(
            email=email,
            hashed_password=None,
            is_verified=user_info.is_email_verified and not email.is_synthetic(),
        )

        role = await uow.roles.get_by_name_with_permissions(name=account.role_name)
        if role is None:
            raise RoleDomainError(errors={"role": f"Роль {account.role_name} не найдена"})

        await uow.accounts.save(account=account)
        await uow.account_roles.assign_role(create_account_role(account.id, role.id))
        await uow.oauth_accounts.create(
            create_oauth_account(
                account_id=account.id,
                provider=provider,
                provider_user_id=user_info.provider_user_id,
            )
        )

        return account, role
