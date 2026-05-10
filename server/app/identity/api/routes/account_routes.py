"""
identy/api/routes/account_routes.py

HTTP-роуты для аккаунтов.
"""

from fastapi import APIRouter, Body, Depends, Path, status
from presentation.rest.dependencies.auth import get_current_account
from presentation.rest.dependencies.services import get_account_service, get_password_service

from identity.api.schemas.account import AccountResponse, ResetPasswordRequest
from identity.application.account.service import AccountService
from identity.application.password.commands import ResetPasswordCommand
from identity.application.password.service import PasswordService
from identity.domain.entities.account import Account


router: APIRouter = APIRouter(prefix="/account", tags=["Accounts"])


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    """Получение информации о своем аккаунте. Используется для отображения информации на клиенте"""
    return AccountResponse.from_domain(account=account)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest = Body(...),
    service: PasswordService = Depends(get_password_service),
) -> None:
    """
    Установить новый пароль по токену из письма.

    Токен — из ссылки вида `/reset-password?token=...` в письме.
    После успеха все активные сессии аккаунта отзываются.
    """
    command: ResetPasswordCommand = payload.to_command()
    await service.reset_password(command=command)


@router.get(path="/{account_id:str}", status_code=status.HTTP_200_OK)
async def get_account(
    account_id: str = Path(min_length=32, max_length=32),
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    account: Account = await service.get_account(account_id=account_id)
    return AccountResponse.from_domain(account=account)
