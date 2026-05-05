"""
identity/application/auth/service.py

AuthService — application-сервис аутентификации.

DIP (Dependency Inversion Principle):
  AuthService зависит от портов IPasswordHasher и ITokenService.
  Конкретные реализации (bcrypt, PyJWT) передаются через конструктор.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import secrets

from shared.domain.exceptions import AuthenticationError
from shared.infrastructure.db.settings import settings

from identity.application.auth.commands import LoginCommand, RegisterCommand, TokenPair
from identity.domain.entities.account import Account, create_account
from identity.domain.entities.refresh_token import create_refresh_token
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.ports.token_service import ITokenService
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.hashed_password import HashedPassword
from identity.infrastructure.auth.blacklist_service import blacklist_token
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

    # ── Register ──────────────────────────────────────────────────────────────

    async def register(self, cmd: RegisterCommand) -> Account:
        # Валидация силы пароля — бизнес-правило домена
        HashedPassword.validate_strength(cmd.password)

        email = Email.create(cmd.email)
        hashed = HashedPassword(value=self._hasher.hash(cmd.password))

        async with self._uow_factory.create() as uow:
            existing = await uow.accounts.get_by_email(email.value)
            if existing is not None:
                raise AuthenticationError(
                    message="Email уже занят",
                    errors={"email": "already_exists"},
                )
            account = create_account(email=email, hashed_password=hashed)
            return await uow.accounts.save(account)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, cmd: LoginCommand) -> TokenPair:
        email = Email.create(cmd.email)

        async with self._uow_factory.create() as uow:
            account = await uow.accounts.get_by_email(email.value)
            if account is None or not self._hasher.verify(cmd.password, str(account.hashed_password)):
                raise AuthenticationError(
                    message="Неверный email или пароль",
                    errors={"credentials": "invalid"},
                )
            if account.is_acc_blocked:
                raise AuthenticationError(
                    message="Аккаунт заблокирован",
                    errors={"account": "blocked"},
                )

            session_id = secrets.token_hex(16)
            token_pair = self._tokens.create_token_pair(
                account_id=account.id,
                email=account.email_str,
                role=account.role_str,
                session_id=session_id,
            )

            rt = create_refresh_token(
                account_id=account.id,
                session_id=session_id,
                token_hash=token_pair.refresh_token_hash,
                expires_at=datetime.now(tz=UTC) + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS),
                user_agent=cmd.user_agent,
                ip_address=cmd.ip_address,
            )
            await uow.refresh_tokens.create(rt)

        return TokenPair(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            role=account.role_str,
            permissions=sorted(account.permissions),
        )

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        """Token rotation с детектом компрометации."""
        payload = self._tokens.decode_refresh_token(raw_refresh_token)

        session_id: str = payload.get("sid", "")
        account_id: str = payload.get("sub", "")
        raw_jti: str = payload.get("jti", "")

        async with self._uow_factory.create() as uow:
            rt = await uow.refresh_tokens.get_by_session_id(session_id)

            if rt is None:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"token": "session_not_found"},
                )

            if rt.revoked:
                logger.warning(
                    "Refresh token reuse detected for account %s session %s. Revoking all sessions.",
                    account_id,
                    session_id,
                )
                await uow.refresh_tokens.revoke_all_by_account(account_id)
                raise AuthenticationError(
                    message="Токен уже использован. Все сессии отозваны.",
                    errors={"token": "reuse_detected"},
                )

            if not self._tokens.verify_token_hash(raw_jti, rt.token_hash):
                raise AuthenticationError(
                    message="Токен не совпадает с сессией",
                    errors={"token": "hash_mismatch"},
                )

            await uow.refresh_tokens.revoke_by_session_id(session_id)

            account = await uow.accounts.get_by_id(account_id)
            new_token_pair = self._tokens.create_token_pair(
                account_id=account_id,
                email=account.email_str,
                role=account.role_str,
                session_id=session_id,
            )

            new_rt = create_refresh_token(
                account_id=account_id,
                session_id=session_id,
                token_hash=new_token_pair.refresh_token_hash,
                expires_at=datetime.now(tz=UTC) + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS),
                user_agent=rt.user_agent,
                ip_address=rt.ip_address,
            )
            await uow.refresh_tokens.create(new_rt)

        return TokenPair(
            access_token=new_token_pair.access_token,
            refresh_token=new_token_pair.refresh_token,
            role=account.role_str,
            permissions=sorted(account.permissions),
        )

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(
        self,
        account_id: str,
        session_id: str | None,
        access_token: str | None = None,
    ) -> None:
        """
        Logout из текущей сессии.

        access_token передаётся вместо payload — сервис сам вычисляет TTL.
        session_id=None допустим (только blacklist без revoke refresh).
        """
        if access_token:
            try:
                payload = self._tokens.decode_access_token(access_token)
                ttl = self._tokens.get_access_token_ttl(access_token)
                await blacklist_token(payload.jti, ttl)
            except AuthenticationError:
                pass  # токен уже истёк — blacklist не нужен

        if session_id is not None:
            async with self._uow_factory.create() as uow:
                await uow.refresh_tokens.revoke_by_session_id(session_id)

    async def logout_all(
        self,
        account_id: str,
        access_token: str | None = None,
    ) -> None:
        """Logout со всех устройств. Revoke всех refresh tokens аккаунта."""
        if access_token:
            try:
                payload = self._tokens.decode_access_token(access_token)
                ttl = self._tokens.get_access_token_ttl(access_token)
                await blacklist_token(payload.jti, ttl)
            except AuthenticationError:
                pass

        async with self._uow_factory.create() as uow:
            await uow.refresh_tokens.revoke_all_by_account(account_id)

    # ── Sessions ──────────────────────────────────────────────────────────────

    async def get_sessions(self, account_id: str) -> list:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.refresh_tokens.get_active_by_account(account_id)

    async def revoke_session(self, account_id: str, session_id: str) -> None:
        async with self._uow_factory.create() as uow:
            rt = await uow.refresh_tokens.get_by_session_id(session_id)
            if rt is None or rt.account_id != account_id:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"session": "not_found"},
                )
            await uow.refresh_tokens.revoke_by_session_id(session_id)
