import asyncio
import logging
import time

from shared.infrastructure.db.enums import CircuitBreakerState
from shared.infrastructure.db.settings import settings


logger = logging.getLogger(__name__)

_FAILURE_THRESHOLD = 3
_RECOVERY_TIMEOUT = 30.0


class CircuitBreaker:
    def __init__(self) -> None:
        self._state = CircuitBreakerState.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        if self._state == CircuitBreakerState.CLOSED:
            return True
        if self._state == CircuitBreakerState.OPEN:
            if time.monotonic() - self._opened_at >= _RECOVERY_TIMEOUT:
                self._state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN — один probe

    async def record_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._state = CircuitBreakerState.CLOSED

    async def record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= _FAILURE_THRESHOLD or self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "Redis circuit breaker OPEN — кэш и blacklist недоступны. Access tokens валидны до %d мин.",
                    settings.JWT_TOKEN_ACCESS_LIFETIME_MINUTES,
                )
