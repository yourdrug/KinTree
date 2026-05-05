"""
identity/infrastructure/refresh_token/repositories.py

SQLAlchemy-реализация RefreshTokenRepository.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Result, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.entities.refresh_token import RefreshToken as DomainRefreshToken
from identity.infrastructure.db.models.refresh_token import RefreshToken as RefreshTokenORM
from identity.infrastructure.refresh_token.mapper import RefreshTokenMapper


class RefreshTokenRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, token: DomainRefreshToken) -> DomainRefreshToken:
        """Создаёт новую запись refresh token, возвращает доменный объект."""
        data = RefreshTokenMapper.to_persistence(token)
        stmt = insert(RefreshTokenORM).values(**data).returning(RefreshTokenORM)
        result: Result = await self._session.execute(stmt)
        orm: RefreshTokenORM = result.scalar_one()
        return RefreshTokenMapper.to_domain(orm)

    async def get_by_session_id(self, session_id: str) -> DomainRefreshToken | None:
        result = await self._session.execute(select(RefreshTokenORM).where(RefreshTokenORM.session_id == session_id))
        orm = result.scalar_one_or_none()
        return RefreshTokenMapper.to_domain(orm) if orm else None

    async def get_active_by_account(self, account_id: str) -> list[DomainRefreshToken]:
        """Все активные (не отозванные, не истёкшие) сессии аккаунта."""
        now = datetime.now(tz=UTC)
        result = await self._session.execute(
            select(RefreshTokenORM).where(
                RefreshTokenORM.account_id == account_id,
                RefreshTokenORM.revoked.is_(False),
                RefreshTokenORM.expires_at > now,
            )
        )
        return [RefreshTokenMapper.to_domain(orm) for orm in result.scalars().all()]

    async def revoke_by_session_id(self, session_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenORM).where(RefreshTokenORM.session_id == session_id).values(revoked=True)
        )

    async def revoke_all_by_account(self, account_id: str) -> None:
        """Отзывает все сессии аккаунта. Вызывается при детекте token reuse."""
        await self._session.execute(
            update(RefreshTokenORM).where(RefreshTokenORM.account_id == account_id).values(revoked=True)
        )

    async def delete_expired(self) -> int:
        """Удаляет истёкшие токены. Вызывается из background job."""
        now = datetime.now(tz=UTC)
        result = await self._session.execute(delete(RefreshTokenORM).where(RefreshTokenORM.expires_at <= now))
        return result.rowcount
