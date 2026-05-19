"""
identity/application/email/service.py

EmailService — application-сервис подтверждения email и отправления писем.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import secrets

from shared.domain.exceptions import AccountBlockedError, InvalidEmailTokenError
from shared.infrastructure.db.settings import settings
from shared.infrastructure.utils import hash_raw_str

from identity.application.email.commands import (
    ForgotPasswordCommand,
    SendVerificationEmailCommand,
    VerifyEmailCommand,
)
from identity.domain.entities.account import Account
from identity.domain.entities.email_token import EmailTokenType, create_email_token
from identity.domain.ports.email_sender import IEmailSender
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.infrastructure.email.templates import reset_password_html, verify_email_html
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


# TTL для токенов
_VERIFY_EMAIL_TTL_MINUTES = 60
_RESET_PASSWORD_TTL_MINUTES = 15


class EmailService:
    """Application-сервис email-подтверждения и сброса пароля."""

    def __init__(
        self,
        uow_factory: IdentityUoWFactory,
        email_sender: IEmailSender,
        password_hasher: IPasswordHasher,
    ) -> None:
        self._uow_factory = uow_factory
        self._sender = email_sender
        self._hasher = password_hasher

    async def send_verification_email(self, command: SendVerificationEmailCommand) -> None:
        """
        Сгенерировать токен верификации и отправить письмо.

        Вызывается:
          - После регистрации (из AuthService.register)
          - По явному запросу (resend_verification endpoint)

        Аннулирует предыдущие токены верификации для этого аккаунта.
        """

        async with self._uow_factory.create(master=True) as uow:
            account: Account = await uow.accounts.get_by_id(account_id=command.account_id)

            if account.is_acc_blocked:
                raise AccountBlockedError()

            if account.email_str.endswith("@telegram.oauth"):
                return  # Telegram-аккаунты не верифицируются по email

            raw_token = secrets.token_urlsafe(32)
            token_hash = hash_raw_str(raw_token)

            expires_at = datetime.now(tz=UTC) + timedelta(minutes=_VERIFY_EMAIL_TTL_MINUTES)
            email_token = create_email_token(
                account_id=command.account_id,
                token_hash=token_hash,
                token_type=EmailTokenType.VERIFY_EMAIL,
                expires_at=expires_at,
            )

            await uow.email_tokens.invalidate_previous(
                account_id=command.account_id,
                token_type=EmailTokenType.VERIFY_EMAIL,
            )
            await uow.email_tokens.create(email_token)

        verify_url = f"{settings.FRONTEND_VERIFY_EMAIL_URL}?token={raw_token}"
        html = verify_email_html(verify_url=verify_url, expires_minutes=_VERIFY_EMAIL_TTL_MINUTES)

        await self._sender.send(
            to=command.email,
            subject="Подтвердите ваш email — KinTree",
            html=html,
        )
        logger.info("Verification email sent to account_id=%s", command.account_id)

    async def verify_email(self, command: VerifyEmailCommand) -> None:
        """
        Подтвердить email по токену из письма.

        Raises:
            InvalidEmailTokenError: если токен не найден, использован или истёк.
        """
        token_hash = hash_raw_str(command.token)

        async with self._uow_factory.create(master=True) as uow:
            email_token = await uow.email_tokens.get_valid_by_hash(
                token_hash=token_hash,
                token_type=EmailTokenType.VERIFY_EMAIL,
            )

            if email_token is None:
                raise InvalidEmailTokenError()

            account = await uow.accounts.get_by_id(email_token.account_id)

            if account.is_acc_blocked:
                raise AccountBlockedError()

            # Идемпотентно: уже подтверждён → просто отметить токен использованным
            if not account.is_verified:
                account.is_verified = True
                await uow.accounts.save(account)

            await uow.email_tokens.mark_used(email_token.id)

        logger.info("Email verified for account_id=%s", email_token.account_id)

    async def forgot_password(self, command: ForgotPasswordCommand) -> None:
        """
        Отправить письмо со ссылкой для сброса пароля.

        Не раскрывает, существует ли аккаунт с таким email
        (одинаковый ответ 204 в любом случае — защита от перебора).
        """
        async with self._uow_factory.create(master=True) as uow:
            account: Account | None = await uow.accounts.get_by_email(command.email)

            if account is None:
                return

            expires_at = datetime.now(tz=UTC) + timedelta(minutes=_RESET_PASSWORD_TTL_MINUTES)
            raw_token = secrets.token_urlsafe(32)
            token_hash = hash_raw_str(raw_token)

            email_token = create_email_token(
                account_id=account.id,
                token_hash=token_hash,
                token_type=EmailTokenType.RESET_PASSWORD,
                expires_at=expires_at,
            )
            await uow.email_tokens.invalidate_previous(account.id, EmailTokenType.RESET_PASSWORD)
            await uow.email_tokens.create(email_token)

        # Письмо — вне транзакции (не блокируем коммит IO)
        reset_url = f"{settings.FRONTEND_RESET_URL}?token={raw_token}"
        html = reset_password_html(reset_url=reset_url, expires_minutes=_RESET_PASSWORD_TTL_MINUTES)
        await self._sender.send(to=command.email, subject="Сброс пароля — KinTree", html=html)
        logger.info("Password reset email sent to account_id=%s", account.id)
