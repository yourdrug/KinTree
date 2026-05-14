"""
identity/domain/value_objects/email.py

Email — Value Object.

Принципы:
- Нормализация (lowercase + strip) происходит при создании объекта.
- Валидация формата — в домене, не в API-схеме.
- Immutable: создать невалидный Email невозможно.
- str(email) возвращает нормализованную строку — удобно для ORM/логов.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from shared.domain.exceptions import DomainValidationError


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_MAX_LENGTH = 254  # RFC 5321
_RESERVED_DOMAINS = {"telegram.oauth", "oauth.internal"}


@dataclass(frozen=True)
class Email:
    """
    Value Object: электронный адрес.

    Идентичность — по значению (нормализованная строка).
    Создание через фабрику Email.create() или конструктор с уже валидным значением.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise DomainValidationError(field="email", message="Email не может быть пустым")
        if len(self.value) > _MAX_LENGTH:
            raise DomainValidationError(field="email", message=f"Email слишком длинный (max {_MAX_LENGTH})")
        if not _EMAIL_RE.match(self.value):
            raise DomainValidationError(field="email", message="Некорректный формат email")

    @classmethod
    def create(cls, raw: str) -> Email:
        """
        Фабрика: нормализует (strip + lowercase) и валидирует.

        Raises:
            DomainValidationError — если формат невалиден.
        """
        normalized = raw.strip().lower()
        domain = normalized.split("@")[-1] if "@" in normalized else ""

        if domain in _RESERVED_DOMAINS:
            raise DomainValidationError(field="email", message="Зарезервированный домен")
        return cls(value=normalized)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)
