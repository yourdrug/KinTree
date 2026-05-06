"""
identy/application/auth/commands.py

DTO модели для передачи между routes и application слоями
"""

from dataclasses import dataclass


@dataclass
class RegisterCommand:
    email: str
    password: str


@dataclass
class LoginCommand:
    email: str
    password: str
    user_agent: str | None = None
    ip_address: str | None = None


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    role: str
    permissions: list[str]
