"""
application/auth/service.py

Сервис аутентификации.
При логине/рефреше возвращает TokenPair вместе с разрешениями аккаунта.
"""

from __future__ import annotations

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

    async def login(self, command: LoginCommand) -> TokenPair:
        async with self.uow:
            account = await self.repository_facade.account_repository.get_by_email(
                email=command.email,
            )

            if account is None or not verify_password(command.password, account.hashed_password):
                raise AuthenticationError(message="Неверный email или пароль")

            if account.is_acc_blocked:
                raise AccountBlockedError(
                    message="Аккаунт заблокирован",
                    errors={"account": "Ваш аккаунт заблокирован. Обратитесь в поддержку."},
                )

            access_token = create_access_token(
                account_id=account.id,
                email=account.email,
                role=account.role_name,
            )
            refresh_token = create_refresh_token(account_id=account.id)

            await self.repository_facade.account_repository.update_refresh_token(
                account_id=account.id,
                hashed_refresh_token=hash_token(refresh_token),
            )

            return TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                permissions=sorted(account.permissions),
                role=account.role_name,
            )

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_refresh_token(refresh_token)
        account_id: str = payload["sub"]

        async with self.uow:
            account = await self.repository_facade.account_repository.get_by_id(
                account_id=account_id,
            )

            if account.is_acc_blocked:
                raise AccountBlockedError(message="Аккаунт заблокирован")

            if account.refresh_token is None or not verify_token_hash(refresh_token, account.refresh_token):
                raise AuthenticationError(
                    message="Refresh-токен недействителен",
                    errors={"token": "revoked_or_invalid"},
                )

            new_access = create_access_token(
                account_id=account.id,
                email=account.email,
                role=account.role_name,
            )
            new_refresh = create_refresh_token(account_id=account.id)

            await self.repository_facade.account_repository.update_refresh_token(
                account_id=account.id,
                hashed_refresh_token=hash_token(new_refresh),
            )

            return TokenPair(
                access_token=new_access,
                refresh_token=new_refresh,
                permissions=sorted(account.permissions),
                role=account.role_name,
            )

    async def logout(self, account_id: str) -> None:
        async with self.uow:
            await self.repository_facade.account_repository.update_refresh_token(
                account_id=account_id,
                hashed_refresh_token=None,
            )
