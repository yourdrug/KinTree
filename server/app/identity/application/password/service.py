"""
identity/application/password/service.py

PasswordService — управление паролями аккаунта.
"""

from __future__ import annotations

import logging

from shared.domain.exceptions import InvalidEmailTokenError
from shared.infrastructure.db.settings import settings
from shared.infrastructure.utils import hash_raw_str

from identity.application.password.commands import ChangePasswordCommand, ResetPasswordCommand
from identity.domain.entities.email_token import EmailTokenType
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.value_objects.hashed_password import HashedPassword
from identity.infrastructure.auth.blacklist_service import blacklist_session
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


class PasswordService:
    def __init__(
        self,
        uow_factory: IdentityUoWFactory,
        password_hasher: IPasswordHasher,
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = password_hasher

    async def reset_password(self, command: ResetPasswordCommand) -> None:
        """
        Сбросить пароль по токену из письма.

        1. Валидирует силу пароля (доменный инвариант).
        2. Проверяет токен — не истёк, не использован, тип RESET_PASSWORD.
        3. Меняет пароль.
        4. Отзывает все активные сессии + blacklist в Redis.

        Raises:
            InvalidEmailTokenError: токен не найден, использован или истёк.
        """
        HashedPassword.validate_strength(command.new_password)
        token_hash = hash_raw_str(command.token)

        async with self._uow_factory.create(master=True) as uow:
            email_token = await uow.email_tokens.get_valid_by_hash(
                token_hash=token_hash,
                token_type=EmailTokenType.RESET_PASSWORD,
            )
            if email_token is None:
                raise InvalidEmailTokenError()

            account = await uow.accounts.get_by_id(email_token.account_id)
            account.hashed_password = HashedPassword(value=self._hasher.hash(command.new_password))
            await uow.accounts.save(account)
            await uow.email_tokens.mark_used(email_token.id)

            ttl = settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60
            active_sessions = await uow.refresh_tokens.get_active_by_account(account.id)
            await uow.refresh_tokens.revoke_all_by_account(account.id)

        for session in active_sessions:
            await blacklist_session(session.session_id, ttl)

        logger.info("Password reset completed for account_id=%s", email_token.account_id)

    async def change_password(self, command: ChangePasswordCommand) -> None:
        """Смена пароля аутентифицированным пользователем."""
        ...
