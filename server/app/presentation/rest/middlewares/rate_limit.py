"""
presentation/rest/middleware/rate_limit.py

Rate limiting как настоящий Starlette middleware.
Регистрируется через app.add_middleware(RateLimitMiddleware).

Fail-open: при недоступности Redis пропускает запрос.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from shared.infrastructure.cache.redis_client import RedisClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from presentation.rest.dependencies.request_meta import get_request_meta


logger = logging.getLogger(__name__)

_cache = RedisClient.namespace("ratelimit")


# action → (max_requests, window_seconds)
_LIMITS: dict[str, tuple[int, int]] = {
    "login": (5, 60),
    "refresh": (10, 60),
    "register": (3, 600),
    "forgot_password": (3, 3600),
    "verify_email": (10, 60),
    "resend_verification": (3, 3600),
}

# path suffix → action
_PATH_MAP: dict[str, str] = {
    "/auth/login": "login",
    "/auth/cookie/login": "login",
    "/auth/refresh": "refresh",
    "/auth/cookie/refresh": "refresh",
    "/auth/register": "register",
    "/auth/cookie/register": "register",
    "/auth/forgot-password": "forgot_password",
    "/auth/verify-email": "verify_email",
    "/auth/resend-verification": "resend_verification",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware: проверяет rate limit для защищённых эндпоинтов.

    Только POST-запросы проверяются (login, refresh, register).
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "POST":
            action = _PATH_MAP.get(request.url.path)
            if action:
                response = await self._check(request, action)
                if response:
                    return response

        return await call_next(request)

    async def _check(self, request: Request, action: str) -> JSONResponse | None:
        max_requests, window_seconds = _LIMITS[action]
        ip = get_request_meta(request).ip_address
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
