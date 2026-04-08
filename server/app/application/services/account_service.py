from domain.models.account import Account
from infrastructure.common.services import BaseService


class AccountService(BaseService):
    async def get_account(self, account_id: str) -> dict:
        async with self.uow:
            account: Account = await self.repository_facade.account_repository.get_account(
                account_id=account_id,
            )

            return {"account_id": account.id, "email": account.email}
