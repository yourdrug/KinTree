"""
identity/application/oauth/commands.py

DTO для OAuth use-cases.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GoogleCallbackCommand:
    """Данные от Google после редиректа."""

    code: str
    user_agent: str | None = None
    ip_address: str | None = None


@dataclass
class TelegramCallbackCommand:
    """
    Данные от Telegram Login Widget.

    Telegram присылает GET-параметры:
      id, first_name, last_name, username, photo_url, auth_date, hash
    """

    telegram_id: str
    first_name: str
    last_name: str | None
    username: str | None
    photo_url: str | None
    auth_date: int
    hash: str
    user_agent: str | None = None
    ip_address: str | None = None
