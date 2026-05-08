"""
identity/api/routes/email_routes.py

Роуты подтверждения email и сброса пароля.

Endpoints:
  POST /auth/verify-email          — подтвердить email по токену
  POST /auth/resend-verification   — повторно отправить письмо подтверждения
  POST /auth/forgot-password       — запросить сброс пароля (отправить письмо)
  POST /auth/reset-password        — установить новый пароль по токену

Принципы:
  - forgot-password всегда возвращает 204 — не раскрываем существование аккаунта.
  - resend-verification требует аутентификации — отправляем на email текущего аккаунта.
  - verify-email и reset-password публичные — токен из письма и есть аутентификация.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status
from presentation.rest.dependencies.auth import get_current_account
from presentation.rest.dependencies.services import get_email_service

from identity.api.schemas.email import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from identity.application.email.commands import SendVerificationEmailCommand
from identity.application.email.service import EmailService
from identity.domain.entities.account import Account


router: APIRouter = APIRouter(prefix="/auth", tags=["Auth · Email"])


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    payload: VerifyEmailRequest = Body(...),
    service: EmailService = Depends(get_email_service),
) -> None:
    """
    Подтвердить email по токену из письма.

    Токен — из ссылки вида `/verify-email?token=...` в письме.
    После успеха аккаунт получает `is_verified=True`.
    """
    await service.verify_email(payload.to_command())


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    account: Account = Depends(get_current_account),
    service: EmailService = Depends(get_email_service),
) -> None:
    """
    Повторно отправить письмо подтверждения email.

    Требует аутентификации. Аннулирует предыдущий токен верификации.
    Если email уже подтверждён — всё равно возвращает 204 (идемпотентно).
    """
    command = SendVerificationEmailCommand(
        account_id=account.id,
        email=account.email_str,
    )
    await service.send_verification_email(command)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    payload: ForgotPasswordRequest = Body(...),
    service: EmailService = Depends(get_email_service),
) -> None:
    """
    Запросить сброс пароля.

    Отправляет письмо на указанный email, если аккаунт существует.
    Всегда возвращает 204 — не раскрывает, зарегистрирован ли email.
    """
    await service.forgot_password(payload.to_command())


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest = Body(...),
    service: EmailService = Depends(get_email_service),
) -> None:
    """
    Установить новый пароль по токену из письма.

    Токен — из ссылки вида `/reset-password?token=...` в письме.
    После успеха все активные сессии аккаунта отзываются.
    """
    await service.reset_password(payload.to_command())
