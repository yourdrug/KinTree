"""
identity/application/auth/service.py

AuthService — ядро аутентификации.
"""

from __future__ import annotations

import logging
import secrets

from shared.domain.exceptions import AuthenticationError

from identity.application.auth.commands import LoginCommand, RegisterCommand, TokenPair
from identity.domain.entities.account import Account, create_account
from identity.infrastructure.auth.blacklist_service import blacklist_token
from identity.infrastructure.auth.jwt_service import (
    access_token_ttl_seconds,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
    verify_token_hash,
)
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, uow_factory: IdentityUoWFactory) -> None:
        self._uow_factory = uow_factory

    # ── Register ──────────────────────────────────────────────────────────────

    async def register(self, cmd: RegisterCommand) -> Account:
        """Регистрация. Логика не менялась."""
        from identity.infrastructure.auth.jwt_service import hash_password

        async with self._uow_factory.create() as uow:
            existing = await uow.accounts.get_by_email(cmd.email)
            if existing:
                raise AuthenticationError(
                    message="Email уже занят",
                    errors={"email": "already_exists"},
                )

            domain_account: Account = create_account(
                email=cmd.email,
                hashed_password=hash_password(cmd.password),
            )

            account = await uow.accounts.save(domain_account)
            return account

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, cmd: LoginCommand) -> TokenPair:
        """
        1. Проверяем credentials
        2. Генерируем session_id
        3. Создаём access + refresh токены
        4. Сохраняем refresh hash в БД
        5. Возвращаем пару
        """
        async with self._uow_factory.create() as uow:
            account = await uow.accounts.get_by_email(cmd.email)
            if not account or not verify_password(cmd.password, account.hashed_password):
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

            access_token, _jti = create_access_token(
                account_id=str(account.id),
                email=account.email,
                role=account.role_name,
                session_id=session_id,
            )
            refresh_token, token_hash = create_refresh_token(
                account_id=str(account.id),
                session_id=session_id,
            )

            await uow.refresh_tokens.create(
                account_id=str(account.id),
                session_id=session_id,
                token_hash=token_hash,
                user_agent=cmd.user_agent,
                ip_address=cmd.ip_address,
            )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            role=account.role_name,
            permissions=sorted(account.permissions),
        )

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        """
        Token rotation с детектом компрометации.

        Сценарий компрометации:
          Атакующий украл refresh token и использовал его раньше легитимного
          пользователя. При следующем использовании легитимный пользователь
          получит ошибку (токен revoked). Мы детектируем это и отзываем ВСЕ
          сессии аккаунта — атакующий теряет доступ.
        """
        try:
            payload = decode_refresh_token(raw_refresh_token)
        except AuthenticationError:
            raise

        session_id: str = payload.get("sid", "")
        account_id: str = payload.get("sub", "")
        # jti refresh токена = raw hex, который мы положили в JWT
        raw_jti: str = payload.get("jti", "")

        async with self._uow_factory.create() as uow:
            rt = await uow.refresh_tokens.get_by_session_id(session_id)

            if rt is None:
                # Токен не найден в БД вообще — невалиден
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"token": "session_not_found"},
                )

            if rt.revoked:
                # Токен reuse — потенциальная компрометация
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

            if not verify_token_hash(raw_jti, rt.token_hash):
                raise AuthenticationError(
                    message="Токен не совпадает с сессией",
                    errors={"token": "hash_mismatch"},
                )

            # Всё ок — ротируем
            await uow.refresh_tokens.revoke_by_session_id(session_id)

            # Создаём новый токен с тем же session_id
            account = await uow.accounts.get_by_id(account_id)
            if not account:
                raise AuthenticationError(message="Аккаунт не найден")

            new_refresh_token, new_token_hash = create_refresh_token(
                account_id=account_id,
                session_id=session_id,
            )

            access_token, _jti = create_access_token(
                account_id=account_id,
                email=account.email,
                role=account.role_name,
                session_id=session_id,
            )

            # Создаём новую запись (старая revoked=True остаётся для аудита)
            await uow.refresh_tokens.create(
                account_id=account_id,
                session_id=session_id,
                token_hash=new_token_hash,
                user_agent=rt.user_agent,
                ip_address=rt.ip_address,
            )

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
            role=account.role_name,
            permissions=sorted(account.permissions),
        )

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(
        self,
        account_id: str,
        session_id: str | None = None,
        access_token_payload: dict | None = None,
    ) -> None:
        """
        Logout из текущей сессии.

        1. Добавляем jti access token в Redis blacklist (если токен ещё жив)
        2. Revoke refresh token в БД
        """
        # Blacklist access token по jti
        if access_token_payload:
            jti = access_token_payload.get("jti")
            if jti:
                ttl = access_token_ttl_seconds(access_token_payload)
                await blacklist_token(jti, ttl)

        if not session_id:
            return

        async with self._uow_factory.create() as uow:
            await uow.refresh_tokens.revoke_by_session_id(session_id)

    async def logout_all(
        self,
        account_id: str,
        access_token_payload: dict | None = None,
    ) -> None:
        """
        Logout со всех устройств.
        Access tokens текущей сессии кладём в blacklist.
        Все refresh tokens аккаунта — revoke.
        """
        if access_token_payload:
            jti = access_token_payload.get("jti")
            if jti:
                ttl = access_token_ttl_seconds(access_token_payload)
                await blacklist_token(jti, ttl)

        async with self._uow_factory.create() as uow:
            await uow.refresh_tokens.revoke_all_by_account(account_id)

    # ── Sessions ──────────────────────────────────────────────────────────────

    async def get_sessions(self, account_id: str) -> list:
        """Список активных сессий для UI."""
        async with self._uow_factory.create() as uow:
            return await uow.refresh_tokens.get_active_by_account(account_id)

    async def revoke_session(self, account_id: str, session_id: str) -> None:
        """Revoke конкретной сессии (например, 'выйти с телефона')."""
        async with self._uow_factory.create() as uow:
            rt = await uow.refresh_tokens.get_by_session_id(session_id)

            if not rt or str(rt.account_id) != account_id:
                raise AuthenticationError(
                    message="Сессия не найдена",
                    errors={"session": "not_found"},
                )

            await uow.refresh_tokens.revoke_by_session_id(session_id)
