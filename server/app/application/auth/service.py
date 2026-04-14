"""
application/auth/service.py

Orchestrates all authentication use-cases.
Has zero knowledge of HTTP or JWT internals — those live in the infrastructure layer.
"""

from domain.entities.account import Account, create_account
from domain.exceptions import (
    AccountAlreadyExistsError,
    AccountBlockedError,
    AuthenticationError,
)
from infrastructure.auth.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from infrastructure.common.services import BaseService

from application.auth.dto import LoginCommand, RegisterCommand, TokenPair


class AuthService(BaseService):
    # ── Register ───────────────────────────────────────────────────────────────

    async def register(self, command: RegisterCommand) -> Account:
        async with self.uow:
            existing = await self.repository_facade.account_repository.get_by_email(
                email=command.email,
            )
            if existing is not None:
                raise AccountAlreadyExistsError(
                    message="Аккаунт уже существует",
                    errors={"email": "Этот email уже зарегистрирован"},
                )

            account = create_account(
                email=command.email,
                hashed_password=hash_password(command.password),
            )

            return await self.repository_facade.account_repository.create(account)

    # ── Login ──────────────────────────────────────────────────────────────────

    async def login(self, command: LoginCommand) -> TokenPair:
        async with self.uow:
            account = await self.repository_facade.account_repository.get_by_email(
                email=command.email,
            )

            if account is None or not verify_password(command.password, account.hashed_password):
                # Deliberately vague — do not reveal which part is wrong
                raise AuthenticationError(
                    message="Неверный email или пароль",
                )

            if account.is_acc_blocked:
                raise AccountBlockedError(
                    message="Аккаунт заблокирован",
                    errors={"account": "Ваш аккаунт заблокирован. Обратитесь в поддержку."},
                )

            access_token = create_access_token(account_id=account.id, email=account.email)
            refresh_token = create_refresh_token(account_id=account.id)

            await self.repository_facade.account_repository.update_refresh_token(
                account_id=account.id,
                hashed_refresh_token=hash_token(refresh_token),
            )

            return TokenPair(access_token=access_token, refresh_token=refresh_token)

    # ── Refresh ────────────────────────────────────────────────────────────────

    async def refresh(self, refresh_token: str) -> TokenPair:
        """
        Validates the incoming refresh token, rotates it, and returns a new pair.
        Rotation means the old refresh token is immediately invalidated.
        """
        payload = decode_refresh_token(refresh_token)
        account_id: str = payload["sub"]

        async with self.uow:
            account = await self.repository_facade.account_repository.get_by_id(
                account_id=account_id,
            )

            if account.is_acc_blocked:
                raise AccountBlockedError(
                    message="Аккаунт заблокирован",
                )

            # Verify the token against the stored hash (prevents replay after logout)
            if account.refresh_token is None or not verify_token_hash(refresh_token, account.refresh_token):
                raise AuthenticationError(
                    message="Refresh-токен недействителен",
                    errors={"token": "revoked_or_invalid"},
                )

            # Issue a new pair (rotation)
            new_access = create_access_token(account_id=account.id, email=account.email)
            new_refresh = create_refresh_token(account_id=account.id)

            await self.repository_facade.account_repository.update_refresh_token(
                account_id=account.id,
                hashed_refresh_token=hash_token(new_refresh),
            )

            return TokenPair(access_token=new_access, refresh_token=new_refresh)

    # ── Logout ─────────────────────────────────────────────────────────────────

    async def logout(self, account_id: str) -> None:
        """Clears the stored refresh token, invalidating all active refresh tokens."""
        async with self.uow:
            await self.repository_facade.account_repository.update_refresh_token(
                account_id=account_id,
                hashed_refresh_token=None,
            )
