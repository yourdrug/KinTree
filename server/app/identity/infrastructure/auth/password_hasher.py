"""
identity/infrastructure/auth/password_hasher.py

Adapter: реализация IPasswordHasher через bcrypt.

Выделен из jwt_service.py, где password utils и token utils
были смешаны в одном модуле (нарушение SRP).

Регистрируется в DI-контейнере (dependencies.py) и передаётся
в AuthService через конструктор.
"""

from __future__ import annotations

import bcrypt

from identity.domain.ports.password_hasher import IPasswordHasher


class BcryptPasswordHasher:
    """Adapter: хэширование паролей через bcrypt."""

    def hash(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except Exception:
            return False


# Синглтон — bcrypt stateless, создавать каждый раз не нужно
_hasher: IPasswordHasher = BcryptPasswordHasher()


def get_password_hasher() -> IPasswordHasher:
    """FastAPI dependency / фабрика для DI."""
    return _hasher
