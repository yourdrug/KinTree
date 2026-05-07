"""
identity/application/oauth/service.py

OAuthService — application-сервис OAuth авторизации.

Логика одинакова для всех провайдеров:
  1. Верифицировать данные от провайдера (за это отвечают верификаторы)
  2. Найти существующую OAuth-привязку по (provider, provider_user_id)
  3а. Привязка найдена → логин: загрузить Account, выдать токены
  3б. Привязки нет, но email найден → ConflictError (войдите по паролю)
  3в. Привязки нет, email не найден → регистрация: создать Account + привязку
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

from shared.domain.exceptions import AccountBlockedError, ConflictError, RoleDomainError
from shared.infrastructure.db.settings import settings

from identity.application.auth.commands import TokenPair
from identity.application.oauth.commands import GoogleCallbackCommand, TelegramCallbackCommand
from identity.domain.entities.account import Account, create_account
from identity.domain.entities.account_role import AccountRole, create_account_role
from identity.domain.entities.oauth_account import OAuthAccount, OAuthProvider, create_oauth_account
from identity.domain.entities.permission import Role
from identity.domain.entities.refresh_token import RefreshToken, create_refresh_token
from identity.domain.ports.token_service import CreatedTokenPair, ITokenService
from identity.domain.value_objects.email import Email
from identity.infrastructure.oauth.google_verifier import GoogleUserInfo, get_google_user_info
from identity.infrastructure.oauth.telegram_verifier import TelegramUserInfo, verify_telegram_auth
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


class OAuthService:
    """Application-сервис OAuth авторизации."""

    def __init__(
        self,
        uow_factory: IdentityUoWFactory,
        token_service: ITokenService,
    ) -> None:
        self._uow_factory = uow_factory
        self._tokens = token_service

    async def google_callback(self, command: GoogleCallbackCommand) -> TokenPair:
        """
        Обработать callback от Google (Authorization Code flow).

        Raises:
            ConflictError: email уже зарегистрирован через пароль
            AccountBlockedError: аккаунт заблокирован
            ValueError: невалидный code или id_token
        """
        user_info: GoogleUserInfo = await get_google_user_info(command.code)

        return await self._login_or_register(
            provider=OAuthProvider.GOOGLE,
            provider_user_id=user_info.sub,
            email=user_info.email,
            user_agent=command.user_agent,
            ip_address=command.ip_address,
        )

    async def telegram_callback(self, command: TelegramCallbackCommand) -> TokenPair:
        """
        Обработать данные от Telegram Login Widget.

        Raises:
            ConflictError: крайне редко — если telegram_id уже привязан к другому аккаунту
            AccountBlockedError: аккаунт заблокирован
            ValueError: невалидная подпись Telegram
        """
        user_info: TelegramUserInfo = verify_telegram_auth(
            telegram_id=command.telegram_id,
            first_name=command.first_name,
            last_name=command.last_name,
            username=command.username,
            photo_url=command.photo_url,
            auth_date=command.auth_date,
            hash=command.hash,
        )

        # Telegram может не давать email.
        # Используем синтетический email-like идентификатор для создания аккаунта.
        synthetic_email: str = f"tg_{user_info.telegram_id}@telegram.oauth"

        return await self._login_or_register(
            provider=OAuthProvider.TELEGRAM,
            provider_user_id=user_info.telegram_id,
            email=synthetic_email,
            user_agent=command.user_agent,
            ip_address=command.ip_address,
        )

    async def _login_or_register(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
        email: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenPair:
        """
        Общая логика: найти или создать аккаунт, выдать токены.
        """
        async with self._uow_factory.create() as uow:
            # 1. Ищем существующую OAuth-привязку
            oauth_account: OAuthAccount | None = await uow.oauth_accounts.get_by_provider(
                provider=provider,
                provider_user_id=provider_user_id,
            )

            if oauth_account is not None:
                # Привязка есть → логин
                account: Account = await uow.accounts.get_by_id(oauth_account.account_id)

                if account.is_acc_blocked:
                    raise AccountBlockedError()

            else:
                # Привязки нет — проверяем email (только для провайдеров с реальным email)
                if not email.endswith("@telegram.oauth"):
                    existing: Account | None = await uow.accounts.get_by_email(email)
                    if existing is not None:
                        raise ConflictError(
                            message="Email уже зарегистрирован",
                            errors={
                                "email": "Аккаунт с этим email уже существует. Войдите по паролю.",
                            },
                        )

                # Регистрация нового аккаунта
                validated_email = Email.create(email)

                account = create_account(
                    email=validated_email,
                    hashed_password=None,  # OAuth-аккаунт без пароля
                )

                role: Role | None = await uow.roles.get_by_name(name=account.role_name)
                if role is None:
                    raise RoleDomainError(
                        errors={"role": f"Не найдена роль {account.role_name}"},
                    )

                account_role: AccountRole = create_account_role(
                    account_id=account.id,
                    role_id=role.id,
                )

                await uow.accounts.save(account=account)
                await uow.account_roles.assign_role(account_role=account_role)

                # Создать OAuth-привязку
                new_oauth = create_oauth_account(
                    account_id=account.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                )
                await uow.oauth_accounts.create(new_oauth)

                # Загрузить аккаунт с пермишенами
                account = await uow.accounts.get_by_id(account.id)

            # 2. Создать сессию и выдать токены
            session_id: str = self._tokens.generate_session_id_hex()
            token_pair: CreatedTokenPair = self._tokens.create_token_pair(
                account_id=account.id,
                email=account.email_str,
                role=account.role_str,
                session_id=session_id,
            )

            refresh_token: RefreshToken = create_refresh_token(
                account_id=account.id,
                session_id=session_id,
                token_hash=token_pair.refresh_token_hash,
                expires_at=datetime.now(tz=UTC) + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS),
                user_agent=user_agent,
                ip_address=ip_address,
            )
            await uow.refresh_tokens.create(refresh_token)

        return TokenPair(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            role=account.role_str,
            permissions=sorted(account.permissions),
        )
