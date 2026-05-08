"""
identity/application/password/commands.py
"""

from dataclasses import dataclass


@dataclass
class ResetPasswordCommand:
    token: str
    new_password: str


@dataclass
class ChangePasswordCommand:
    account_id: str
    old_password: str
    new_password: str
