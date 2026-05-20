"""
identity/application/auth/service.py

AuthService — application-сервис аутентификации.
"""

from __future__ import annotations

import logging

from shared.domain.exceptions import (
    AccountDomainError,
    AuthenticationError,
    ConflictError,
)
from shared.domain.permissions.enums import RoleName
from shared.infrastructure.db.settings import settings

from identity.application.auth.commands import LoginCommand, RegisterCommand, TokenPair
from identity.domain.entities.account import Account, create_account
from identity.domain.entities.account_role import create_account_role
from identity.domain.entities.permission import Role
from identity.domain.entities.refresh_token import RefreshToken
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.ports.token_service import AccessTokenPayload, ITokenService
from identity.domain.services.session_service import CreatedSession, SessionDomainService
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.hashed_password import HashedPassword
from identity.infrastructure.auth.blacklist_service import blacklist_session, blacklist_token
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        uow_factory: IdentityUoWFactory,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = password_hasher
        self._tokens = token_service
        self._session_service = SessionDomainService(
            token_service=token_service,
            refresh_ttl_days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS,
        )

    async def register(self, command: RegisterCommand) -> Account:
        """
        Регистрация нового аккаунта.

        Raises:
            AccountDomainError: если пароль слабый.
            ConflictError: если email уже занят.
        """
        HashedPassword.validate_strength(command.password)
        email = Email.create(command.email)
        hashed = HashedPassword(value=self._hasher.hash(command.password))

        async with self._uow_factory.create(master=True) as uow:
            existing: Account | None = await uow.accounts.get_by_email(email.value)

            if existing is not None:
                raise ConflictError(
                    message="Пользователь с таким email уже зарегистрирован",
                    errors={"email": "already_exists"},
                )

            role: Role | None = await uow.roles.get_by_name_with_permissions(name=RoleName.USER)

            if role is None:
                raise AccountDomainError(errors={"role": "Роль USER не найдена в БД"})

            account = create_account(email=email, hashed_password=hashed)
            account_role = create_account_role(account_id=account.id, role_id=role.id)

            saved = await uow.accounts.save(account=account)
            await uow.account_roles.assign_role(account_role=account_role)

        return Account(
            id=saved.id,
            email=saved.email,
            hashed_password=saved.hashed_password,
            is_acc_blocked=saved.is_acc_blocked,
            is_verified=saved.is_verified,
            permissions=role.codenames,
            role_name=account.role_name,
        )

    async def login(self, command: LoginCommand) -> TokenPair:
        """
        Raises:
            AuthenticationError: если email/пароль неверны.
            AccountBlockedError: если аккаунт заблокирован.
        """
        email = Email.create(command.email)

        async with self._uow_factory.create(master=True) as uow:
            account = await uow.accounts.get_by_email(email.value)

            if account is None or not self._hasher.verify(
                command.password,
                str(account.hashed_password),
            ):
                raise AuthenticationError(
                    message="Неверный email или пароль",
                    errors={"credentials": "invalid"},
                )

            account.check_not_blocked()

            session = self._session_service.create_session(
                account=account,
                user_agent=command.user_agent,
                ip_address=command.ip_address,
            )
            await uow.refresh_tokens.create(session.refresh_token)

        return _to_token_pair(session, account)

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        """
        Token rotation с детектом компрометации (reuse detection).

        Raises:
            AuthenticationError: невалидный токен, reuse, hash mismatch.
            AccountBlockedError: аккаунт заблокирован.
        """
        payload = self._tokens.decode_refresh_token(raw_refresh_token)
        session_id: str = payload["sid"]
        account_id: str = payload["sub"]
        raw_jti: str = payload["jti"]

        async with self._uow_factory.create(master=True) as uow:
            stored_token = await uow.refresh_tokens.get_by_session_id(session_id)

            if stored_token is None:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"token": "session_not_found"},
                )

            if stored_token.revoked:
                logger.warning(
                    "Token reuse detected: account_id=%s session_id=%s — revoking all sessions",
                    account_id,
                    session_id,
                )
                await uow.refresh_tokens.revoke_all_by_account(account_id)
                raise AuthenticationError(
                    message="Токен уже использован. Все сессии отозваны.",
                    errors={"token": "reuse_detected"},
                )

            if not self._tokens.verify_token_hash(raw_jti, stored_token.token_hash):
                raise AuthenticationError(
                    message="Токен не совпадает с сессией",
                    errors={"token": "hash_mismatch"},
                )

            await uow.refresh_tokens.revoke_by_session_id(session_id)

            account = await uow.accounts.get_by_id(account_id)
            account.check_not_blocked()

            session = self._session_service.rotate_session(
                account=account,
                existing_session_id=session_id,
                user_agent=stored_token.user_agent,
                ip_address=stored_token.ip_address,
            )
            await uow.refresh_tokens.create(session.refresh_token)

        return _to_token_pair(session, account)

    async def logout(self, raw_token: str) -> None:
        """Logout из текущей сессии. Невалидный токен — silent no-op."""
        try:
            payload: AccessTokenPayload = self._tokens.decode_access_token_unverified(raw_token)
        except AuthenticationError:
            return

        ttl = self._tokens.get_access_token_ttl(raw_token)
        await blacklist_token(payload.jti, ttl)

        async with self._uow_factory.create(master=True) as uow:
            await uow.refresh_tokens.revoke_by_session_id(payload.session_id)

    async def logout_all(self, account_id: str) -> None:
        """Logout со всех устройств."""
        ttl = settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60

        async with self._uow_factory.create(master=True) as uow:
            active_sessions = await uow.refresh_tokens.get_active_by_account(account_id)
            await uow.refresh_tokens.revoke_all_by_account(account_id)

        for session in active_sessions:
            await blacklist_session(session.session_id, ttl)

    async def get_sessions(self, account_id: str) -> list[RefreshToken]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.refresh_tokens.get_active_by_account(account_id)

    async def revoke_session(self, account_id: str, session_id: str) -> None:
        async with self._uow_factory.create(master=True) as uow:
            token = await uow.refresh_tokens.get_by_session_id(session_id)

            if token is None or token.account_id != account_id:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"session": "not_found"},
                )

            await uow.refresh_tokens.revoke_by_session_id(session_id)

        ttl = settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60
        await blacklist_session(session_id, ttl)


def _to_token_pair(session: CreatedSession, account: Account) -> TokenPair:
    """Конвертация внутреннего результата сессии в публичный DTO."""
    return TokenPair(
        access_token=session.access_token,
        refresh_token=session.raw_refresh_token,
        role=account.role_str,
        permissions=sorted(account.permissions),
    )
