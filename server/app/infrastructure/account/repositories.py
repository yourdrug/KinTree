from sqlalchemy import select
from sqlalchemy.engine.result import Result
from sqlalchemy.sql import Select

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.account import Account


class AccountRepository(BaseRepository):
    async def get_account(self, account_id: str) -> Account:
        statement: Select = select(Account).where(Account.id == account_id)
        result: Result = await self.session.execute(statement)
        account: Account = result.scalar_one()

        return account
