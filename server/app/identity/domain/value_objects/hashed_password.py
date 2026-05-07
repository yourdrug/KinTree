"""
identity/domain/value_objects/hashed_password.py

HashedPassword — Value Object.

Принципы:
- Домен знает, что пароль хэширован — но НЕ знает алгоритм (bcrypt, argon2 и т.д.).
- Хэширование происходит в infrastructure через IPasswordHasher (Port).
- Домен только хранит непустой хэш и умеет убеждаться в его минимальной длине.
- Валидация силы пароля — здесь же через статический метод validate_strength(),
  чтобы бизнес-правила ("пароль должен иметь цифру") жили в домене, а не в API-схеме.

Что НЕ делает этот VO:
- Не вызывает bcrypt — это инфраструктура.
- Не принимает plain-text пароль — только уже готовый хэш.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from shared.domain.exceptions import DomainValidationError


logger = logging.getLogger(__name__)

_MIN_HASH_LENGTH = 20  # bcrypt = 60 chars; защита от случайной передачи plain-text
_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128


@dataclass(frozen=True)
class HashedPassword:
    """
    Value Object: хэш пароля.

    Создаётся инфраструктурным слоем через IPasswordHasher.
    Домен только хранит и проверяет базовые инварианты хэша.
    """

    value: str | None = None

    def __post_init__(self) -> None:
        if self.value is None:
            return

        value = self.value.strip()

        if not value:
            raise DomainValidationError(field="hashed_password", message="Хэш пароля не может быть пустым")

        if len(value) < _MIN_HASH_LENGTH:
            raise DomainValidationError(
                field="hashed_password",
                message="Значение слишком короткое для хэша пароля",
            )

    def __str__(self) -> str:
        return self.value or ""  # для oauth, мб придумать что получше?

    def __repr__(self) -> str:
        return "HashedPassword(***)"

    @staticmethod
    def validate_strength(plain: str) -> None:
        """
        Проверяет силу plain-text пароля перед хэшированием.
        Бизнес-правило домена — минимальные требования к паролю.

        Вызывается в application-сервисе ДО хэширования:
            HashedPassword.validate_strength(cmd.password)
            hashed = password_hasher.hash(cmd.password)

        Raises:
            DomainValidationError — если пароль слишком слабый.
        """
        errors = []

        if len(plain) < _MIN_PASSWORD_LENGTH:
            errors.append(f"минимум {_MIN_PASSWORD_LENGTH} символов")
        if len(plain) > _MAX_PASSWORD_LENGTH:
            errors.append(f"максимум {_MAX_PASSWORD_LENGTH} символов")
        if not any(c.isupper() for c in plain):
            errors.append("хотя бы одна заглавная буква")
        if not any(c.islower() for c in plain):
            errors.append("хотя бы одна строчная буква")
        if not any(c.isdigit() for c in plain):
            errors.append("хотя бы одна цифра")

        if errors:
            raise DomainValidationError(
                message="Пароль не соответствует требованиям",
                errors={"password": "Пароль должен содержать: " + ", ".join(errors)},
            )
