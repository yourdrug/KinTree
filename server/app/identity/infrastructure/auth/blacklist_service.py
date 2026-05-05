"""
identity/infrastructure/auth/blacklist_service.py

Blacklist access-токенов через Redis namespace.
"""

from __future__ import annotations

from shared.infrastructure.cache.redis_client import RedisClient


_cache = RedisClient.namespace("blacklist")


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Добавляет jti в blacklist. При ttl <= 0 токен уже истёк — no-op."""
    if ttl_seconds <= 0:
        return
    await _cache.set(jti, "1", ttl=ttl_seconds)


async def is_blacklisted(jti: str) -> bool:
    """Проверяет, отозван ли токен. False при недоступности Redis (fail-open)."""
    return await _cache.exists(jti)
