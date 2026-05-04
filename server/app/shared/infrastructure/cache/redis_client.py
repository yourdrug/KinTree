"""
shared/infrastructure/cache/redis_client.py

Redis-клиент с connection pool и circuit breaker.

Circuit breaker защищает приложение от каскадного падения при
недоступности Redis. Если Redis не отвечает — auth запросы проходят
(fail open), но инцидент логируется. Blacklist-проверка при этом
пропускается: атакующий с украденным access токеном получит максимум
JWT_TOKEN_ACCESS_LIFETIME_MINUTES минут — приемлемый риск для genealogy app.

Состояния circuit breaker:
  CLOSED   — Redis работает, все запросы идут нормально
  OPEN     — Redis упал, запросы пропускаются без проверки, логируется WARNING
  HALF_OPEN — после паузы пробуем один ping, решаем переходить ли в CLOSED
"""

from __future__ import annotations

import asyncio
from enum import Enum
import logging
import time

import redis.asyncio as aioredis

from shared.infrastructure.db.settings import settings


logger = logging.getLogger(__name__)


_pool: aioredis.ConnectionPool | None = None


def _get_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            socket_connect_timeout=1.0,
            socket_timeout=0.5,
            retry_on_timeout=False,
            decode_responses=True,
        )
    return _pool


def get_redis() -> aioredis.Redis:
    """Возвращает Redis-клиент из пула. Не открывает соединение само по себе."""
    return aioredis.Redis(connection_pool=_get_pool())


async def close_redis() -> None:
    global _pool
    if _pool:
        r = aioredis.Redis(connection_pool=_pool)
        await r.close()
        _pool = None


# ── Circuit breaker ───────────────────────────────────────────────────────────

_FAILURE_THRESHOLD = 3  # сколько ошибок подряд → OPEN
_RECOVERY_TIMEOUT = 30.0  # секунд в OPEN перед попыткой HALF_OPEN


class _State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class _CircuitBreaker:
    def __init__(self) -> None:
        self._state = _State.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        if self._state == _State.CLOSED:
            return True
        if self._state == _State.OPEN:
            if time.monotonic() - self._opened_at >= _RECOVERY_TIMEOUT:
                self._state = _State.HALF_OPEN
                return True
            return False
        # HALF_OPEN — разрешаем один probe
        return True

    async def record_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._state = _State.CLOSED

    async def record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= _FAILURE_THRESHOLD or self._state == _State.HALF_OPEN:
                self._state = _State.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "Redis circuit breaker OPEN — blacklist checks bypassed. "
                    "Stolen access tokens valid for up to %d min.",
                    settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES,
                )


_breaker = _CircuitBreaker()


async def redis_ping() -> bool:
    """Проверка доступности Redis при старте."""
    try:
        r = get_redis()
        await r.ping()
        return True
    except Exception as exc:
        logger.error("Redis ping failed: %s", exc)
        return False


async def safe_redis_get(key: str) -> str | None:
    """
    Безопасный GET с circuit breaker.
    Возвращает None как при отсутствии ключа, так и при недоступности Redis.
    """
    if not _breaker.available:
        return None
    try:
        r = get_redis()
        value = await r.get(key)
        await _breaker.record_success()
        return value
    except Exception as exc:
        logger.warning("Redis GET %s failed: %s", key, exc)
        await _breaker.record_failure()
        return None


async def safe_redis_setex(key: str, ttl_seconds: int, value: str) -> bool:
    """
    Безопасный SETEX с circuit breaker.
    Возвращает True при успехе, False при ошибке.
    """
    if not _breaker.available:
        return False
    try:
        r = get_redis()
        await r.setex(key, ttl_seconds, value)
        await _breaker.record_success()
        return True
    except Exception as exc:
        logger.warning("Redis SETEX %s failed: %s", key, exc)
        await _breaker.record_failure()
        return False


async def safe_redis_delete(key: str) -> bool:
    if not _breaker.available:
        return False
    try:
        r = get_redis()
        await r.delete(key)
        await _breaker.record_success()
        return True
    except Exception as exc:
        logger.warning("Redis DELETE %s failed: %s", key, exc)
        await _breaker.record_failure()
        return False
