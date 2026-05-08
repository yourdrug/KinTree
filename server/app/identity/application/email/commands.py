"""
identity/application/email/commands.py

DTO для email use-cases.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SendVerificationEmailCommand:
    account_id: str
    email: str


@dataclass
class VerifyEmailCommand:
    token: str


@dataclass
class ForgotPasswordCommand:
    email: str


@dataclass
class ResetPasswordCommand:
    token: str
    new_password: str
