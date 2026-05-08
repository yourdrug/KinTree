from fastapi import APIRouter, Body, Depends, status
from presentation.rest.dependencies.auth import get_current_account, get_current_token_payload
from presentation.rest.dependencies.services import get_auth_service, get_email_service

from identity.api.schemas.auth import AccountResponse, RegisterRequest
from identity.api.schemas.session import SessionResponse
from identity.application.auth.commands import RegisterCommand
from identity.application.auth.service import AuthService
from identity.application.email.commands import SendVerificationEmailCommand
from identity.application.email.service import EmailService
from identity.domain.entities.account import Account
from identity.domain.entities.refresh_token import RefreshToken
from identity.domain.ports.token_service import AccessTokenPayload


router: APIRouter = APIRouter(prefix="/auth", tags=["Auth · Common"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service),
) -> AccountResponse:
    """Регистрация нового пользователя"""
    command: RegisterCommand = payload.to_command()
    account: Account = await service.register(command=command)

    await email_service.send_verification_email(
        SendVerificationEmailCommand(
            account_id=account.id,
            email=account.email_str,
        )
    )

    return AccountResponse.from_domain(account=account)


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    """Получение информации о своем аккаунте. Используется для отображения информации на клиенте"""
    return AccountResponse.from_domain(account=account)


@router.get("/sessions", status_code=status.HTTP_200_OK)
async def get_all_accounts_sessions(
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> list[SessionResponse]:
    """Получение всех сессий для определенного аккаунта."""

    sessions: list[RefreshToken] = await service.get_sessions(token_payload.account_id)

    return [SessionResponse.from_domain(session=session, token_payload=token_payload) for session in sessions]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    token_payload: AccessTokenPayload = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Завершить конкретную сессию пользователя."""

    await service.revoke_session(
        account_id=token_payload.account_id,
        session_id=session_id,
    )
