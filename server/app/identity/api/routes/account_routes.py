from identity.application.account.service import AccountService
from identity.domain.entities.account import Account
from fastapi import (
    APIRouter,
    Depends,
    Path,
    status,
)

from presentation.rest.dependencies.dependencies import get_account_service


router: APIRouter = APIRouter(prefix="/account", tags=["Accounts"])


@router.get(path="/{account_id:str}", status_code=status.HTTP_200_OK)
async def get_account(
    account_id: str = Path(min_length=32, max_length=32),
    service: AccountService = Depends(get_account_service),
) -> Account:
    account: Account = await service.get_account(
        account_id=account_id,
    )

    return account
