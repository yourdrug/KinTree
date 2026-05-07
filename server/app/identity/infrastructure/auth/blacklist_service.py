"""
identity/infrastructure/auth/blacklist_service.py

Blacklist access-токенов через Redis namespace.
"""

from __future__ import annotations

from shared.infrastructure.cache.redis_client import RedisClient


_cache = RedisClient.namespace("blacklist")
_session_cache = RedisClient.namespace("session_blacklist")


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Добавляет jti в blacklist. При ttl <= 0 токен уже истёк — no-op."""
    if ttl_seconds <= 0:
        return
    await _cache.set(jti, "1", ttl=ttl_seconds)


async def is_blacklisted(jti: str) -> bool:
    """Проверяет, отозван ли токен. False при недоступности Redis (fail-open)."""
    return await _cache.exists(jti)


async def blacklist_session(session_id: str, ttl: int) -> None:
    """Занести session_id в blacklist. Fail-safe: ошибка Redis не пробрасывается."""
    await _session_cache.set(session_id, "1", ttl=ttl)


async def is_session_blacklisted(session_id: str) -> bool:
    """Проверить, отозвана ли сессия. Fail-open: при недоступности Redis возвращает False."""
    return await _session_cache.exists(session_id)
