"""
presentation/rest/middleware/rate_limit.py

Rate limiting для auth эндпоинтов через Redis.

Реализация: sliding window counter.
Ключ: ratelimit:{action}:{identifier}
TTL автоматически сбрасывается при каждом hit — это fixed window, не sliding.
Для genealogy app этого достаточно.

Лимиты (настроены консервативно для auth):
  login:   5 попыток / 1 минуту на IP
  refresh: 10 попыток / 1 минуту на IP
  register: 3 попытки / 10 минут на IP

Fail-open: если Redis недоступен — пропускаем rate limiting, логируем.
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from shared.infrastructure.cache.redis_client import get_redis


logger = logging.getLogger(__name__)

_LIMITS: dict[str, tuple[int, int]] = {
    # action: (max_requests, window_seconds)
    "login": (5, 60),
    "refresh": (10, 60),
    "register": (3, 600),
}


def _get_client_ip(request: Request) -> str:
    """Извлекает реальный IP с учётом reverse proxy."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request, action: str) -> JSONResponse | None:
    """
    Проверяет rate limit для действия.
    Возвращает JSONResponse 429 если лимит превышен, иначе None.

    Использование в роуте:
        if resp := await check_rate_limit(request, "login"):
            return resp
    """
    limit_cfg = _LIMITS.get(action)
    if not limit_cfg:
        return None

    max_requests, window_seconds = limit_cfg
    ip = _get_client_ip(request)
    key = f"ratelimit:{action}:{ip}"

    try:
        r = get_redis()
        count = await r.incr(key)
        if count == 1:
            # Первый хит — устанавливаем TTL
            await r.expire(key, window_seconds)
        if count > max_requests:
            ttl = await r.ttl(key)
            logger.warning(
                "Rate limit exceeded: action=%s ip=%s count=%d",
                action,
                ip,
                count,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Слишком много попыток. Попробуйте через {ttl} сек.",
                    "retry_after": ttl,
                },
                headers={"Retry-After": str(ttl)},
            )
    except Exception as exc:
        # Fail-open: Redis недоступен — пропускаем rate limit
        logger.warning("Rate limit Redis error for %s: %s", action, exc)

    return None
