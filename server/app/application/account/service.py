from domain.entities.account import Account

from application.uow_factory import UoWFactory


class AccountService:
    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    async def get_account(self, account_id: str) -> Account:
        async with self._uow_factory.create(master=False) as uow:
            account: Account = await uow.accounts.get_by_id(
                account_id=account_id,
            )

            return account
