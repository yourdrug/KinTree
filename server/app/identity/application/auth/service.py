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

from shared.domain.exceptions import AccountBlockedError, AccountDomainError, AuthenticationError, RoleDomainError
from shared.infrastructure.db.settings import settings

from identity.application.auth.commands import LoginCommand, RegisterCommand, TokenPair
from identity.domain.entities.account import Account, create_account
from identity.domain.entities.account_role import AccountRole, create_account_role
from identity.domain.entities.permission import Role
from identity.domain.entities.refresh_token import RefreshToken, create_refresh_token
from identity.domain.ports.password_hasher import IPasswordHasher
from identity.domain.ports.token_service import AccessTokenPayload, CreatedTokenPair, ITokenService
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.hashed_password import HashedPassword
from identity.infrastructure.auth.blacklist_service import blacklist_session, blacklist_token
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


class AuthService:
    """Сервис аутентификации"""

    def __init__(
        self,
        uow_factory: IdentityUoWFactory,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = password_hasher
        self._tokens = token_service

    async def register(self, command: RegisterCommand) -> Account:
        HashedPassword.validate_strength(command.password)
        email = Email.create(command.email)

        hashed = HashedPassword(value=self._hasher.hash(command.password))

        async with self._uow_factory.create() as uow:
            existing: Account | None = await uow.accounts.get_by_email(email.value)

            if existing is not None:
                raise AccountDomainError(
                    errors={"email": "Пользователь с таким email уже зарегистрирован."},
                )

            account: Account = create_account(email=email, hashed_password=hashed)
            role: Role | None = await uow.roles.get_by_name(name=account.role_name)

            if role is None:
                raise RoleDomainError(
                    errors={"role": f"Не найдена роль {account.role_name}"},
                )

            account_role: AccountRole = create_account_role(account_id=account.id, role_id=role.id)
            await uow.accounts.save(account=account)
            await uow.account_roles.assign_role(account_role=account_role)

            account_with_permissions: Account = await uow.accounts.get_by_id(account.id)

            return account_with_permissions

    async def login(self, command: LoginCommand) -> TokenPair:
        email = Email.create(command.email)

        async with self._uow_factory.create() as uow:
            account: Account | None = await uow.accounts.get_by_email(email.value)

            if account is None or not self._hasher.verify(command.password, str(account.hashed_password)):
                raise AuthenticationError(
                    message="Неверный email или пароль",
                    errors={"credentials": "Invalid password or email"},
                )

            if account.is_acc_blocked:
                raise AccountBlockedError()

            session_id: str = secrets.token_hex(16)
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
                user_agent=command.user_agent,
                ip_address=command.ip_address,
            )
            await uow.refresh_tokens.create(refresh_token)

        return TokenPair(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            role=account.role_str,
            permissions=sorted(account.permissions),
        )

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        """Token rotation с детектом компрометации."""
        payload: dict = self._tokens.decode_refresh_token(raw_refresh_token)  # TODO доработать типизацию

        session_id: str = payload.get("sid", "")
        account_id: str = payload.get("sub", "")
        raw_jti: str = payload.get("jti", "")

        async with self._uow_factory.create() as uow:
            refresh_token: RefreshToken | None = await uow.refresh_tokens.get_by_session_id(session_id)

            if refresh_token is None:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"token": "session_not_found"},
                )

            if refresh_token.revoked:
                logger.warning(
                    "Обнаружено повторное использование токена обновления для учетной записи %s в сеансе %s. "
                    "Аннулирование всех сеансов.",
                    account_id,
                    session_id,
                )
                await uow.refresh_tokens.revoke_all_by_account(account_id)

                raise AuthenticationError(
                    message="Токен уже использован. Все сессии отозваны.",
                    errors={"token": "reuse_detected"},
                )

            if not self._tokens.verify_token_hash(raw_jti, refresh_token.token_hash):
                raise AuthenticationError(
                    message="Токен не совпадает с сессией",
                    errors={"token": "hash_mismatch"},
                )

            await uow.refresh_tokens.revoke_by_session_id(session_id)

            account: Account = await uow.accounts.get_by_id(account_id)
            new_token_pair: CreatedTokenPair = self._tokens.create_token_pair(
                account_id=account_id,
                email=account.email_str,
                role=account.role_str,
                session_id=session_id,
            )

            new_refresh_token: RefreshToken = create_refresh_token(
                account_id=account_id,
                session_id=session_id,
                token_hash=new_token_pair.refresh_token_hash,
                expires_at=datetime.now(tz=UTC) + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS),
                user_agent=refresh_token.user_agent,
                ip_address=refresh_token.ip_address,
            )
            await uow.refresh_tokens.create(new_refresh_token)

        return TokenPair(
            access_token=new_token_pair.access_token,
            refresh_token=new_token_pair.refresh_token,
            role=account.role_str,
            permissions=sorted(account.permissions),
        )

    async def logout(
        self,
        session_id: str | None,
        access_token: str | None = None,
    ) -> None:
        """
        Logout из текущей сессии.

        access_token передаётся вместо payload — сервис сам вычисляет TTL.
        session_id=None допустим (только blacklist без revoke refresh).
        """
        if access_token:
            payload: AccessTokenPayload = self._tokens.decode_access_token(access_token)
            ttl: int = self._tokens.get_access_token_ttl(access_token)
            await blacklist_token(payload.jti, ttl)

        if session_id is not None:
            async with self._uow_factory.create() as uow:
                await uow.refresh_tokens.revoke_by_session_id(session_id)

    async def logout_all(
        self,
        account_id: str,
    ) -> None:
        """Logout со всех устройств. Revoke всех refresh tokens аккаунта."""
        ttl = settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60

        async with self._uow_factory.create() as uow:
            active_sessions: list[RefreshToken] = await uow.refresh_tokens.get_active_by_account(account_id)
            await uow.refresh_tokens.revoke_all_by_account(account_id)

        for session in active_sessions:
            await blacklist_session(session.session_id, ttl)

    async def get_sessions(self, account_id: str) -> list[RefreshToken]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.refresh_tokens.get_active_by_account(account_id)

    async def revoke_session(self, account_id: str, session_id: str) -> None:
        async with self._uow_factory.create() as uow:
            refresh_token: RefreshToken | None = await uow.refresh_tokens.get_by_session_id(session_id)

            if refresh_token is None or refresh_token.account_id != account_id:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"session": "not_found"},
                )

            await uow.refresh_tokens.revoke_by_session_id(session_id)

        ttl: int = settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES * 60
        await blacklist_session(session_id, ttl)
