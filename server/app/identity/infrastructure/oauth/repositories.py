"""
identity/infrastructure/oauth/repositories.py
"""

from __future__ import annotations

from sqlalchemy import Insert, Select, delete, insert, select
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.entities.oauth_account import OAuthAccount as DomainOAuthAccount
from identity.domain.entities.oauth_account import OAuthProvider
from identity.infrastructure.db.models.oauth_account import OAuthAccount as ORMOAuthAccount
from identity.infrastructure.oauth.mapper import OAuthAccountMapper


class OAuthAccountRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> DomainOAuthAccount | None:
        result = await self._session.scalar(
            select(ORMOAuthAccount).where(
                ORMOAuthAccount.provider == str(provider),
                ORMOAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return OAuthAccountMapper.to_domain(result) if result else None

    async def get_by_account_id(self, account_id: str) -> list[DomainOAuthAccount]:
        statement: Select = select(ORMOAuthAccount).where(ORMOAuthAccount.account_id == account_id)
        results: ScalarResult[ORMOAuthAccount | None] = await self._session.scalars(statement)
        return [OAuthAccountMapper.to_domain(row) for row in results]

    async def create(self, oauth_account: DomainOAuthAccount) -> None:
        data: dict = OAuthAccountMapper.to_persistence(entity=oauth_account)
        statement: Insert = insert(ORMOAuthAccount).values(**data)
        await self._session.execute(statement)

    async def delete(self, oauth_account_id: str) -> None:
        await self._session.execute(delete(ORMOAuthAccount).where(ORMOAuthAccount.id == oauth_account_id))
