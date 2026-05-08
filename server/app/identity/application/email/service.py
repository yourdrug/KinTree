"""
identity/application/email/service.py

EmailService — application-сервис подтверждения email и сброса пароля.

Flows:

  Подтверждение email:
    1. register() → AuthService создаёт аккаунт → вызывает send_verification_email()
    2. send_verification_email() → генерирует токен, сохраняет хэш, отправляет письмо
    3. verify_email() → проверяет токен, ставит account.is_verified = True

  Сброс пароля:
    1. forgot_password() → находит аккаунт по email, отправляет письмо со ссылкой
    2. reset_password() → проверяет токен, обновляет пароль аккаунта

Безопасность:
  - raw токен = secrets.token_urlsafe(32), хранится только SHA-256 хэш
  - Перед выдачей нового токена аннулируются все предыдущие (invalidate_previous)
  - forgot_password() не раскрывает, существует ли аккаунт (одинаковый ответ)
  - Токены одноразовые (mark_used после валидации)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import logging
import secrets

from shared.domain.exceptions import InvalidEmailTokenError
from shared.infrastructure.db.settings import settings

from identity.application.email.commands import (
    ForgotPasswordCommand,
    ResetPasswordCommand,
    SendVerificationEmailCommand,
    VerifyEmailCommand,
)
from identity.domain.entities.account import Account
from identity.domain.entities.email_token import EmailTokenType, create_email_token
from identity.domain.ports.email_sender import IEmailSender
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.value_objects.hashed_password import HashedPassword
from identity.infrastructure.auth.blacklist_service import blacklist_session
from identity.infrastructure.email.templates import reset_password_html, verify_email_html
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger("default")

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

        expires_at = datetime.now(tz=UTC) + timedelta(minutes=_VERIFY_EMAIL_TTL_MINUTES)

        raw_token = await self._generate_email_token(
            account_id=command.account_id,
            token_type=EmailTokenType.VERIFY_EMAIL,
            expires_at=expires_at,
        )
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
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
        token_hash = self._hash(command.token)

        async with self._uow_factory.create(master=True) as uow:
            email_token = await uow.email_tokens.get_valid_by_hash(
                token_hash=token_hash,
                token_type=EmailTokenType.VERIFY_EMAIL,
            )
            if email_token is None:
                raise InvalidEmailTokenError()

            account = await uow.accounts.get_by_id(email_token.account_id)

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
        raw_token = await self._generate_email_token(
            account_id=account.id,
            token_type=EmailTokenType.RESET_PASSWORD,
            expires_at=expires_at,
        )

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        html = reset_password_html(reset_url=reset_url, expires_minutes=_RESET_PASSWORD_TTL_MINUTES)

        await self._sender.send(
            to=command.email,
            subject="Сброс пароля — KinTree",
            html=html,
        )
        logger.info("Password reset email sent to account_id=%s", account.id)

    async def reset_password(self, command: ResetPasswordCommand) -> None:
        """
        Сбросить пароль по токену из письма.

        Raises:
            InvalidEmailTokenError: если токен не найден, использован или истёк.
        """
        HashedPassword.validate_strength(command.new_password)

        token_hash = self._hash(command.token)

        async with self._uow_factory.create(master=True) as uow:
            email_token = await uow.email_tokens.get_valid_by_hash(
                token_hash=token_hash,
                token_type=EmailTokenType.RESET_PASSWORD,
            )
            if email_token is None:
                raise InvalidEmailTokenError()

            account = await uow.accounts.get_by_id(email_token.account_id)

            new_hashed = self._hasher.hash(command.new_password)
            account.hashed_password = HashedPassword(value=new_hashed)
            await uow.accounts.save(account)

            await uow.email_tokens.mark_used(email_token.id)

            # Отзываем все сессии — пароль сменился, старые refresh tokens недействительны
            ttl = settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60

            active_sessions = await uow.refresh_tokens.get_active_by_account(account.id)
            await uow.refresh_tokens.revoke_all_by_account(account.id)

            for session in active_sessions:
                await blacklist_session(session.session_id, ttl)

        logger.info("Password reset completed for account_id=%s", email_token.account_id)

    async def _generate_email_token(self, account_id: str, token_type: EmailTokenType, expires_at: datetime) -> str:
        raw_token: str = secrets.token_urlsafe(32)
        token_hash: str = self._hash(raw_token)

        email_token = create_email_token(
            account_id=account_id,
            token_hash=token_hash,
            token_type=token_type,
            expires_at=expires_at,
        )

        async with self._uow_factory.create(master=True) as uow:
            await uow.email_tokens.invalidate_previous(
                account_id=account_id,
                token_type=token_type,
            )
            await uow.email_tokens.create(email_token)

        return raw_token

    @staticmethod
    def _hash(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()
