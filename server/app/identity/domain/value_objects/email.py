"""
identity/domain/value_objects/email.py

Email — Value Object.

Изменения:
- is_synthetic() — метод самого объекта. Единственное место в системе
  где определено что такое «синтетический email».
  Раньше эта логика была размазана по трём файлам:
    - _RESERVED_DOMAINS в Email.create()
    - _SYNTHETIC_EMAIL_DOMAINS в oauth/service.py
    - проверка суффикса .endswith("@telegram.oauth") в email/service.py

  Теперь: email.is_synthetic() — и больше ничего нигде.

- _SYNTHETIC_DOMAINS вынесен на уровень модуля как приватная константа,
  используется и в create() (запрет регистрации), и в is_synthetic().
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from shared.domain.exceptions import DomainValidationError


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_MAX_LENGTH = 254  # RFC 5321

# Домены зарезервированы для OAuth-провайдеров без реального email.
# Пользователь не может зарегистрироваться с таким доменом через форму.
# Используется в: create() (запрет) и is_synthetic() (проверка).
_SYNTHETIC_DOMAINS: frozenset[str] = frozenset(
    {
        "telegram.oauth",
        "oauth.internal",
    }
)


@dataclass(frozen=True)
class Email:
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
        Фабрика: нормализует и валидирует.
        Запрещает синтетические домены — пользователь не может их зарегистрировать.

        Raises:
            DomainValidationError — если формат невалиден или домен зарезервирован.
        """
        normalized = raw.strip().lower()
        domain = normalized.split("@")[-1] if "@" in normalized else ""

        if domain in _SYNTHETIC_DOMAINS:
            raise DomainValidationError(field="email", message="Зарезервированный домен")

        return cls(value=normalized)

    @classmethod
    def create_synthetic(cls, raw: str) -> Email:
        """
        Фабрика для синтетических email OAuth-провайдеров.
        Обходит проверку зарезервированных доменов — только для инфраструктурного слоя.

        Используется в: TelegramOAuthProvider, будущих провайдерах без email.
        """
        normalized = raw.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise DomainValidationError(field="email", message="Некорректный формат synthetic email")
        return cls(value=normalized)

    @classmethod
    def from_provider(cls, raw: str) -> Email:
        """
        Фабрика для email от OAuth-провайдеров.
        Сам определяет синтетический или реальный — вызывающий код не думает об этом.

        Используется в: OAuthService._register.
        """
        normalized = raw.strip().lower()
        domain = normalized.split("@")[-1] if "@" in normalized else ""
        if domain in _SYNTHETIC_DOMAINS:
            return cls.create_synthetic(normalized)
        return cls.create(normalized)

    def is_synthetic(self) -> bool:
        """
        Синтетический email — от OAuth-провайдера без реального email (Telegram).

        Единственное место в системе где определена эта логика.
        Используется в:
          - OAuthService: пропустить проверку на существующий аккаунт
          - EmailService: не отправлять письмо верификации
        """
        domain = self.value.split("@")[-1] if "@" in self.value else ""
        return domain in _SYNTHETIC_DOMAINS

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
