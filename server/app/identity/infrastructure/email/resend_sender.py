"""
identity/infrastructure/email/resend_sender.py

Adapter: реализация IEmailSender через Resend HTTP API.

Используется resend-python SDK
При недоступности Resend бросает EmailSendError (ServerException → 500).

Синглтон: _sender создаётся один раз при импорте модуля.
Resend stateless — повторная инициализация не нужна.
"""

from __future__ import annotations

import logging

import resend
from shared.domain.exceptions import EmailSendError
from shared.infrastructure.db.settings import settings

from identity.domain.ports.email_sender import IEmailSender


logger = logging.getLogger("default")


class ResendEmailSender:
    """Adapter: отправка писем через Resend."""

    def __init__(self, api_key: str, from_address: str) -> None:
        resend.api_key = api_key
        self._from = from_address

    async def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
    ) -> None:
        """
        Отправить письмо через Resend.

        Raises:
            EmailSendError: при любой ошибке Resend API.
        """

        try:
            params: resend.Emails.SendParams = {
                "from": self._from,
                "to": [to],
                "subject": subject,
                "html": html,
            }

            await resend.Emails.send_async(params)
            logger.info("Email sent to %s subject=%r", to, subject)
        except Exception as exc:
            logger.error("Resend API error: %s", exc, exc_info=True)
            raise EmailSendError(detail=str(exc)) from exc


_sender: IEmailSender = ResendEmailSender(
    api_key=settings.RESEND_API_KEY,
    from_address=settings.EMAIL_FROM,
)


def get_email_sender() -> IEmailSender:
    """FastAPI dependency / фабрика."""
    return _sender
