"""
identity/infrastructure/auth/blacklist_service.py

Blacklist access токенов через Redis.

Ключ:   blacklist:{jti}
Значие: "1"
TTL:    остаток жизни access token (чтобы запись самоудалилась)

Fail-open: если Redis недоступен — check возвращает False (пропускает).
Это сознательный компромисс для genealogy app:
  - Сервис не падает из-за Redis
  - Атакующий с украденным токеном получит максимум 10 минут доступа
  - Circuit breaker в redis_client логирует инцидент
"""

from __future__ import annotations

from shared.infrastructure.cache.redis_client import safe_redis_get, safe_redis_setex


_PREFIX = "blacklist"


def _key(jti: str) -> str:
    return f"{_PREFIX}:{jti}"


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """
    Добавляет jti в blacklist с TTL = остаток жизни токена.
    При ttl <= 0 токен уже истёк — ничего не делаем.
    """
    if ttl_seconds <= 0:
        return
    await safe_redis_setex(_key(jti), ttl_seconds, "1")


async def is_blacklisted(jti: str) -> bool:
    """
    Проверяет, отозван ли токен.
    Возвращает False при недоступности Redis (fail-open).
    """
    value = await safe_redis_get(_key(jti))
    return value is not None
