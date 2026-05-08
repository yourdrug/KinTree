"""
identity/infrastructure/email_token/repositories.py

SQLAlchemy-реализация EmailTokenRepository.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Result, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.entities.email_token import EmailToken as DomainEmailToken
from identity.domain.entities.email_token import EmailTokenType
from identity.infrastructure.db.models.email_token import EmailToken as EmailTokenORM
from identity.infrastructure.email_token.mapper import EmailTokenMapper


class EmailTokenRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, token: DomainEmailToken) -> DomainEmailToken:
        data = EmailTokenMapper.to_persistence(token)
        stmt = insert(EmailTokenORM).values(**data).returning(EmailTokenORM)
        result: Result = await self._session.execute(stmt)
        orm: EmailTokenORM = result.scalar_one()
        return EmailTokenMapper.to_domain(orm)

    async def get_valid_by_hash(
        self,
        token_hash: str,
        token_type: EmailTokenType,
    ) -> DomainEmailToken | None:
        now = datetime.now(tz=UTC)
        result: Result = await self._session.execute(
            select(EmailTokenORM).where(
                EmailTokenORM.token_hash == token_hash,
                EmailTokenORM.token_type == token_type.value,
                EmailTokenORM.is_used.is_(False),
                EmailTokenORM.expires_at > now,
            )
        )
        orm = result.scalar_one_or_none()
        return EmailTokenMapper.to_domain(orm) if orm else None

    async def mark_used(self, token_id: str) -> None:
        await self._session.execute(update(EmailTokenORM).where(EmailTokenORM.id == token_id).values(is_used=True))

    async def invalidate_previous(
        self,
        account_id: str,
        token_type: EmailTokenType,
    ) -> None:
        """Помечает все активные токены данного типа как использованные."""
        await self._session.execute(
            update(EmailTokenORM)
            .where(
                EmailTokenORM.account_id == account_id,
                EmailTokenORM.token_type == token_type.value,
                EmailTokenORM.is_used.is_(False),
            )
            .values(is_used=True)
        )

    async def delete_expired(self) -> int:
        now = datetime.now(tz=UTC)
        result = await self._session.execute(delete(EmailTokenORM).where(EmailTokenORM.expires_at <= now))
        return result.rowcount
