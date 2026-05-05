"""
presentation/rest/middleware/rate_limit.py

Rate limiting через Redis namespace "ratelimit".
"""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from shared.infrastructure.cache.redis_client import RedisClient


logger = logging.getLogger(__name__)

_cache = RedisClient.namespace("ratelimit")

_LIMITS: dict[str, tuple[int, int]] = {
    "login": (5, 60),
    "refresh": (10, 60),
    "register": (3, 600),
}


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request, action: str) -> JSONResponse | None:
    """
    Проверяет rate limit. Возвращает JSONResponse 429 или None.
    Fail-open: при недоступности Redis пропускает.
    """
    limit_cfg = _LIMITS.get(action)
    if not limit_cfg:
        return None

    max_requests, window_seconds = limit_cfg
    ip = _get_client_ip(request)
    key = f"{action}:{ip}"

    count = await _cache.incr(key)
    if count is None:
        logger.warning("Rate limit skipped (Redis unavailable): action=%s ip=%s", action, ip)
        return None

    if count == 1:
        await _cache.expire(key, window_seconds)

    if count > max_requests:
        retry_after = max(await _cache.ttl(key), 0)
        logger.warning("Rate limit exceeded: action=%s ip=%s count=%d", action, ip, count)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "message": "Слишком много попыток",
                "errors": {"retry_after": retry_after},
            },
            headers={"Retry-After": str(retry_after)},
        )

    return None
