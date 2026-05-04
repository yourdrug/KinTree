"""
identity/infrastructure/refresh_token/repositories.py

Репозиторий для работы с refresh_tokens.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from shared.infrastructure.db.settings import settings
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.infrastructure.db.models.refresh_token import RefreshToken


class RefreshTokenRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        account_id: str,
        session_id: str,
        token_hash: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """Создаёт новую запись refresh token."""
        expires_at = datetime.now(tz=UTC) + timedelta(days=settings.JWT_TOKEN_REFRESH_LIFETIME_DAYS)
        rt = RefreshToken(
            account_id=account_id,
            session_id=session_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._session.add(rt)
        await self._session.flush()
        return rt

    async def get_by_session_id(self, session_id: str) -> RefreshToken | None:
        result = await self._session.execute(select(RefreshToken).where(RefreshToken.session_id == session_id))
        return result.scalar_one_or_none()

    async def get_active_by_account(self, account_id: str) -> list[RefreshToken]:
        """Все активные (не отозванные, не истёкшие) сессии аккаунта."""
        now = datetime.now(tz=UTC)
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.account_id == account_id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
        )
        return list(result.scalars().all())

    async def revoke_by_session_id(self, session_id: str) -> None:
        """Отзывает одну сессию."""
        await self._session.execute(
            update(RefreshToken).where(RefreshToken.session_id == session_id).values(revoked=True)
        )

    async def revoke_all_by_account(self, account_id: str) -> None:
        """
        Отзывает все сессии аккаунта.
        Вызывается при детекте компрометации (token reuse).
        """
        await self._session.execute(
            update(RefreshToken).where(RefreshToken.account_id == account_id).values(revoked=True)
        )

    async def delete_expired(self) -> int:
        """Очистка истёкших токенов. Вызывается из background job."""
        now = datetime.now(tz=UTC)
        result = await self._session.execute(delete(RefreshToken).where(RefreshToken.expires_at <= now))
        return result.rowcount
