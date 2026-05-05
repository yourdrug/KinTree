"""
identity/domain/ports/password_hasher.py

Port: интерфейс хэширования паролей.
"""

from __future__ import annotations

from typing import Protocol


class IPasswordHasher(Protocol):
    """Port: хэширование и проверка паролей."""

    def hash(self, plain: str) -> str:
        """Хэширует plain-text пароль. Возвращает строку для хранения в БД."""
        ...

    def verify(self, plain: str, hashed: str) -> bool:
        """Проверяет plain против хэша. Возвращает True если совпадает."""
        ...
