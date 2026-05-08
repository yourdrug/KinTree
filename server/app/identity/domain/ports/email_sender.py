"""
identity/domain/ports/email_sender.py

Port: интерфейс отправки email.

Домен не знает про Resend, SMTP и т.д.
Конкретная реализация передаётся через DI.
"""

from __future__ import annotations

from typing import Protocol


class IEmailSender(Protocol):
    """Port: отправка писем."""

    async def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
    ) -> None:
        """
        Отправить письмо.

        Args:
            to:      Email получателя.
            subject: Тема письма.
            html:    HTML-тело письма.

        Raises:
            EmailSendError: если письмо не удалось отправить.
        """
        ...
