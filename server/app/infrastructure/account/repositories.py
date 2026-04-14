from domain.entities.account import Account as DomainAccount
from domain.repositories.account import AbstractAccountRepository
from sqlalchemy import select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import Select

from infrastructure.account.account_mapper import AccountORMMapper
from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.account import Account


class AccountRepository(BaseRepository, AbstractAccountRepository):

    async def exists(self, object_id: str) -> bool:
        return await self._check_exists(object_id=object_id, model=Account)

    async def get_by_id(self, account_id: str) -> DomainAccount:
        statement: Select = select(Account).where(Account.id == account_id)
        result: Result = await self.session.execute(statement)
        account: Account = result.scalar_one()
        return AccountORMMapper.to_domain(account)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        statement: Select = select(Account).where(Account.email == email)
        result: Result = await self.session.execute(statement)
        account: Account | None = result.scalar_one_or_none()
        if account is None:
            return None
        return AccountORMMapper.to_domain(account)

    async def create(self, account: DomainAccount) -> DomainAccount:
        from sqlalchemy import insert
        data = AccountORMMapper.to_persistence(account)
        from sqlalchemy import insert as sa_insert
        statement = sa_insert(Account).values(**data).returning(Account)
        result: Result = await self.session.execute(statement)
        orm_account: Account = result.scalar_one()
        return AccountORMMapper.to_domain(orm_account)

    async def update_refresh_token(
        self,
        account_id: str,
        hashed_refresh_token: str | None,
    ) -> None:
        statement = (
            update(Account)
            .where(Account.id == account_id)
            .values(refresh_token=hashed_refresh_token)
        )
        await self.session.execute(statement)
