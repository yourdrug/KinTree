"""
api/schemas/auth.py
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from identity.application.auth.commands import LoginCommand, RegisterCommand


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass1!"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = []
        if not any(c.isupper() for c in v):
            errors.append("хотя бы одна заглавная буква")
        if not any(c.islower() for c in v):
            errors.append("хотя бы одна строчная буква")
        if not any(c.isdigit() for c in v):
            errors.append("хотя бы одна цифра")
        if errors:
            raise ValueError("Пароль должен содержать: " + ", ".join(errors))
        return v

    def to_command(self) -> RegisterCommand:
        return RegisterCommand(email=self.email, password=self.password)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, examples=["StrongPass1!"])

    def to_command(self) -> LoginCommand:
        return LoginCommand(email=self.email, password=self.password)


class TokenResponse(BaseModel):
    """
    Ответ при логине/рефреше.

    permissions — список всех codename разрешений пользователя.
    Клиент может закэшировать и использовать для UI-логики
    (показать/скрыть кнопки) без дополнительных запросов.

    Пример:
        {
          "access_token": "eyJ...",
          "refresh_token": "eyJ...",
          "token_type": "bearer",
          "role": "user",
          "permissions": ["family:create", "family:read", "person:create", ...]
        }
    """

    access_token: str
    refresh_token: str
    role: str
    permissions: list[str] = Field(description="Отсортированный список codename всех разрешений пользователя")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class AccountResponse(BaseModel):
    id: str
    email: str
    is_verified: bool
    is_acc_blocked: bool
    role: str
    permissions: list[str]

    model_config = {"from_attributes": True}
