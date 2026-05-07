"""
identity/domain/entities/oauth_provider.py
Наверное куда-то надо перенести, но пока не знаю
"""

from enum import StrEnum


class OAuthProvider(StrEnum):
    GOOGLE = "google"
    TELEGRAM = "telegram"
