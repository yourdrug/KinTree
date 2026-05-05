"""
shared/infrastructure/cache/redis_client.py

RedisClient — универсальный Redis-клиент для кэширования и хранения состояния.

Возможности:
  1. Lifecycle: RedisClient.init() / RedisClient.close() в lifespan FastAPI
  2. Circuit breaker: fail-open при недоступности Redis
  3. Namespace-based кэширование: избегает коллизий между разными модулями
  4. Типизированные операции: get_json / set_json для сложных объектов
  5. TTL helpers: удобные методы с явными именами
  6. FastAPI dependency: get_cache(ns) → CacheNamespace для инжекции

Архитектура namespace:
  Каждый модуль работает в своём "пространстве имён".
  Ключи хранятся как "{namespace}:{key}" — нет коллизий между модулями.

  Примеры:
    blacklist:jti_abc123          (identity.auth)
    ratelimit:login:192.168.1.1   (presentation.middleware)
    family_cache:family_id_xyz    (genealogy.family)
    session_meta:session_id_abc   (identity.session)

Использование в коде:
  # Прямой доступ (для infrastructure-модулей)
  await RedisClient.safe_get("blacklist:jti_abc")

  # Через namespace (рекомендуется)
  cache = RedisClient.namespace("family_cache")
  await cache.set("family_id_xyz", data, ttl=300)
  data = await cache.get_json("family_id_xyz")

  # FastAPI dependency
  async def handler(cache: CacheNamespace = Depends(get_cache("family_cache"))):
      await cache.set_json("key", value, ttl=60)
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import json
import logging
from typing import Any, TypeVar

import redis.asyncio as aioredis

from shared.infrastructure.cache.circuit_breaker import CircuitBreaker
from shared.infrastructure.db.settings import settings


logger = logging.getLogger(__name__)


T = TypeVar("T")


class CacheNamespace:
    """
    Изолированное пространство имён для кэширования.

    Все ключи автоматически префиксируются: "{namespace}:{key}".
    Операции fail-safe — никогда не бросают исключений.

    Получение:
        cache = RedisClient.namespace("my_module")
        # или через FastAPI DI:
        Depends(get_cache("my_module"))
    """

    def __init__(self, namespace: str) -> None:
        if not namespace or ":" in namespace:
            raise ValueError(f"Namespace не может быть пустым или содержать ':' : {namespace!r}")
        self._ns = namespace

    def _key(self, key: str) -> str:
        return f"{self._ns}:{key}"

    # ── String operations ─────────────────────────────────────────────────────

    async def get(self, key: str) -> str | None:
        """Получить строковое значение. None если не найдено или Redis недоступен."""
        return await RedisClient.safe_get(self._key(key))

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """
        Сохранить строковое значение.

        ttl=None → бессрочно (используй с осторожностью).
        ttl=0    → не сохранять (no-op, возвращает True).
        """
        if ttl == 0:
            return True
        if ttl is not None:
            return await RedisClient.safe_setex(self._key(key), ttl, value)
        return await RedisClient.safe_set(self._key(key), value)

    async def delete(self, key: str) -> bool:
        return await RedisClient.safe_delete(self._key(key))

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None

    async def ttl(self, key: str) -> int:
        """Оставшееся TTL в секундах. -1 если бессрочно, -2 если не существует."""
        return await RedisClient.safe_ttl(self._key(key))

    async def expire(self, key: str, ttl: int) -> bool:
        return await RedisClient.safe_expire(self._key(key), ttl)

    # ── JSON operations ───────────────────────────────────────────────────────

    async def get_json(self, key: str) -> Any | None:
        """
        Получить JSON-сериализованное значение.
        None если ключ не найден, Redis недоступен или JSON невалиден.
        """
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Redis: невалидный JSON для ключа %s:%s", self._ns, key)
            return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Сохранить значение как JSON."""
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            logger.warning("Redis: ошибка сериализации JSON для %s:%s: %s", self._ns, key, exc)
            return False
        return await self.set(key, serialized, ttl=ttl)

    # ── Counter operations ────────────────────────────────────────────────────

    async def incr(self, key: str) -> int | None:
        """Атомарный инкремент. None если Redis недоступен."""
        return await RedisClient.safe_incr(self._key(key))

    # ── Bulk operations ───────────────────────────────────────────────────────

    async def get_many(self, keys: list[str]) -> dict[str, str | None]:
        """Получить несколько ключей. Возвращает {key: value | None}."""
        result: dict[str, str | None] = {}
        for key in keys:
            result[key] = await self.get(key)
        return result

    async def delete_many(self, keys: list[str]) -> int:
        """Удалить несколько ключей. Возвращает количество удалённых."""
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    # ── Cache-aside helper ────────────────────────────────────────────────────

    async def get_or_set_json(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int,
    ) -> Any:
        """
        Cache-aside pattern: вернуть из кэша или вычислить и сохранить.

        factory может быть sync или async callable.

        Пример:
            data = await cache.get_or_set_json(
                key=f"family:{family_id}",
                factory=lambda: service.get_family(family_id),
                ttl=300,
            )
        """
        cached = await self.get_json(key)
        if cached is not None:
            return cached

        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        await self.set_json(key, value, ttl=ttl)
        return value


# ── RedisClient ───────────────────────────────────────────────────────────────


class RedisClient:
    """
    Singleton-обёртка над redis.asyncio с connection pool и circuit breaker.

    Lifecycle:
        await RedisClient.init()   # lifespan startup
        await RedisClient.close()  # lifespan shutdown

    Прямой доступ (для infrastructure):
        await RedisClient.safe_get("key")
        await RedisClient.safe_setex("key", 60, "value")

    Namespace-based (рекомендуется):
        cache = RedisClient.namespace("my_module")
        await cache.set_json("key", data, ttl=300)

    FastAPI dependency:
        Depends(get_cache("my_module"))
    """

    _pool: aioredis.ConnectionPool | None = None
    _breaker: CircuitBreaker = CircuitBreaker()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @classmethod
    async def init(cls) -> None:
        """Инициализирует connection pool. Вызывается в lifespan FastAPI."""
        if cls._pool is not None:
            return

        cls._pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            socket_connect_timeout=1.0,
            socket_timeout=0.5,
            retry_on_timeout=False,
            decode_responses=True,
        )

        if await cls.ping():
            logger.info("Redis connected: %s", settings.REDIS_URL)
        else:
            logger.warning(
                "Redis недоступен при старте — кэш, blacklist и rate limiting отключены. REDIS_URL=%s",
                settings.REDIS_URL,
            )

    @classmethod
    async def close(cls) -> None:
        """Закрывает pool. Вызывается в lifespan FastAPI при shutdown."""
        if cls._pool is None:
            return

        client = aioredis.Redis(connection_pool=cls._pool)

        await client.close()
        await cls._pool.disconnect()

        cls._pool = None
        logger.info("Redis disconnected")

    # ── Raw access ────────────────────────────────────────────────────────────

    @classmethod
    def get_client(cls) -> aioredis.Redis:
        """
        Возвращает Redis-клиент из pool.
        Raises RuntimeError если init() не был вызван.
        """
        if cls._pool is None:
            raise RuntimeError("RedisClient не инициализирован. Вызовите await RedisClient.init() в lifespan.")
        return aioredis.Redis(connection_pool=cls._pool)

    # ── Namespace factory ─────────────────────────────────────────────────────

    @classmethod
    def namespace(cls, ns: str) -> CacheNamespace:
        """
        Создаёт изолированное пространство имён.

        Пример:
            blacklist = RedisClient.namespace("blacklist")
            await blacklist.set("jti_abc", "1", ttl=600)
            # Хранится как "blacklist:jti_abc"
        """
        return CacheNamespace(ns)

    # ── Health ────────────────────────────────────────────────────────────────

    @classmethod
    async def ping(cls) -> bool:
        try:
            await cls.get_client().ping()
            return True
        except Exception as exc:
            logger.error("Redis ping failed: %s", exc)
            return False

    # ── Fail-safe primitives с circuit breaker ────────────────────────────────

    @classmethod
    async def safe_get(cls, key: str) -> str | None:
        if not cls._breaker.available:
            return None
        try:
            value = await cls.get_client().get(key)
            await cls._breaker.record_success()
            return value
        except Exception as exc:
            logger.warning("Redis GET %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return None

    @classmethod
    async def safe_set(cls, key: str, value: str) -> bool:
        """SET без TTL."""
        if not cls._breaker.available:
            return False
        try:
            await cls.get_client().set(key, value)
            await cls._breaker.record_success()
            return True
        except Exception as exc:
            logger.warning("Redis SET %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return False

    @classmethod
    async def safe_setex(cls, key: str, ttl_seconds: int, value: str) -> bool:
        """SET с TTL."""
        if not cls._breaker.available:
            return False
        try:
            await cls.get_client().setex(key, ttl_seconds, value)
            await cls._breaker.record_success()
            return True
        except Exception as exc:
            logger.warning("Redis SETEX %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return False

    @classmethod
    async def safe_delete(cls, key: str) -> bool:
        if not cls._breaker.available:
            return False
        try:
            await cls.get_client().delete(key)
            await cls._breaker.record_success()
            return True
        except Exception as exc:
            logger.warning("Redis DELETE %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return False

    @classmethod
    async def safe_incr(cls, key: str) -> int | None:
        if not cls._breaker.available:
            return None
        try:
            value = await cls.get_client().incr(key)
            await cls._breaker.record_success()
            return value
        except Exception as exc:
            logger.warning("Redis INCR %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return None

    @classmethod
    async def safe_expire(cls, key: str, ttl_seconds: int) -> bool:
        if not cls._breaker.available:
            return False
        try:
            await cls.get_client().expire(key, ttl_seconds)
            await cls._breaker.record_success()
            return True
        except Exception as exc:
            logger.warning("Redis EXPIRE %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return False

    @classmethod
    async def safe_ttl(cls, key: str) -> int:
        """TTL в секундах. -1 бессрочно, -2 не существует, 0 при ошибке."""
        if not cls._breaker.available:
            return 0
        try:
            value = await cls.get_client().ttl(key)
            await cls._breaker.record_success()
            return value
        except Exception as exc:
            logger.warning("Redis TTL %s failed: %s", key, exc)
            await cls._breaker.record_failure()
            return 0


# ── FastAPI dependency ────────────────────────────────────────────────────────


def get_cache(namespace: str) -> Callable[[], CacheNamespace]:
    """
    FastAPI dependency factory для namespace-based кэширования.

    Использование в роутах:
        @router.get("/families/{id}")
        async def get_family(
            family_id: str,
            cache: CacheNamespace = Depends(get_cache("family_cache")),
        ):
            return await cache.get_or_set_json(
                key=family_id,
                factory=lambda: service.get_family(family_id),
                ttl=300,
            )
    """
    _ns = CacheNamespace(namespace)

    def _dependency() -> CacheNamespace:
        return _ns

    return _dependency
