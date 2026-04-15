from application.account.service import AccountService
from domain.entities.account import Account
from fastapi import (
    APIRouter,
    Depends,
    Path,
    status,
)

from api.dependencies.base_dependencies import get_service


router: APIRouter = APIRouter(prefix="/account", tags=["Accounts"])


@router.get(path="/{account_id:str}", status_code=status.HTTP_200_OK)
async def get_account(
    account_id: str = Path(min_length=32, max_length=32),
    service: AccountService = Depends(get_service(AccountService, master=False)),
) -> Account:
    account: Account = await service.get_account(
        account_id=account_id,
    )

    return account
