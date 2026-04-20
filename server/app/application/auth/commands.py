"""
application/auth/commands.py
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterCommand:
    email: str
    password: str


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    permissions: list[str]  # отсортированный список codename
    role: str  # имя роли
