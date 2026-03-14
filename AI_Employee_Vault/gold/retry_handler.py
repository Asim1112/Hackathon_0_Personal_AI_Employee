"""
retry_handler.py — Gold Tier Exponential Backoff Utility

Provides a decorator and context manager for retrying flaky operations
(network calls, Playwright automation, API requests) with exponential backoff.

Uses tenacity under the hood for robust retry logic.

Usage:
    from retry_handler import with_retry, RetryConfig

    # Decorator usage
    @with_retry()
    async def fetch_something():
        ...

    # Custom config
    @with_retry(RetryConfig(max_attempts=5, base_delay=2.0))
    async def fragile_call():
        ...

    # Sync functions work too
    @with_retry()
    def sync_operation():
        ...
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Sequence, Type

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    """Maximum number of total attempts (including the first)."""

    base_delay: float = 1.0
    """Initial delay in seconds before the first retry."""

    max_delay: float = 60.0
    """Maximum delay cap in seconds."""

    exponential_base: float = 2.0
    """Multiplier applied to delay on each retry."""

    jitter: bool = True
    """Add ±20% random jitter to prevent thundering herd."""

    retry_on: Sequence[Type[Exception]] = field(
        default_factory=lambda: [Exception]
    )
    """Exception types that trigger a retry. Others propagate immediately."""

    on_retry: Callable[[int, Exception, float], None] | None = None
    """Optional callback called before each retry: (attempt, exception, next_delay)."""


def _compute_delay(attempt: int, config: RetryConfig) -> float:
    """Compute the delay before the next attempt."""
    delay = min(
        config.base_delay * (config.exponential_base ** (attempt - 1)),
        config.max_delay,
    )
    if config.jitter:
        import random
        delay *= 0.8 + random.random() * 0.4  # ±20%
    return delay


def _should_retry(exc: Exception, retry_on: Sequence[Type[Exception]]) -> bool:
    return any(isinstance(exc, exc_type) for exc_type in retry_on)


def with_retry(config: RetryConfig | None = None) -> Callable:
    """
    Decorator that retries a function on failure with exponential backoff.

    Works with both sync and async functions.

    Args:
        config: RetryConfig instance. Defaults to 3 attempts, 1s base delay.

    Example:
        @with_retry(RetryConfig(max_attempts=5, base_delay=2.0))
        async def call_api():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, config.max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        if not _should_retry(exc, config.retry_on):
                            raise
                        last_exc = exc
                        if attempt == config.max_attempts:
                            break
                        delay = _compute_delay(attempt, config)
                        logger.warning(
                            "[retry] %s attempt %d/%d failed: %s — retrying in %.1fs",
                            func.__name__, attempt, config.max_attempts, exc, delay,
                        )
                        if config.on_retry:
                            config.on_retry(attempt, exc, delay)
                        await asyncio.sleep(delay)
                logger.error(
                    "[retry] %s failed after %d attempts: %s",
                    func.__name__, config.max_attempts, last_exc,
                )
                raise last_exc  # type: ignore[misc]

            return async_wrapper

        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, config.max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as exc:
                        if not _should_retry(exc, config.retry_on):
                            raise
                        last_exc = exc
                        if attempt == config.max_attempts:
                            break
                        delay = _compute_delay(attempt, config)
                        logger.warning(
                            "[retry] %s attempt %d/%d failed: %s — retrying in %.1fs",
                            func.__name__, attempt, config.max_attempts, exc, delay,
                        )
                        if config.on_retry:
                            config.on_retry(attempt, exc, delay)
                        time.sleep(delay)
                logger.error(
                    "[retry] %s failed after %d attempts: %s",
                    func.__name__, config.max_attempts, last_exc,
                )
                raise last_exc  # type: ignore[misc]

            return sync_wrapper

    return decorator


# ── Preset configs for common scenarios ──────────────────────────────────────

#: Quick retry for transient network blips (3 attempts, 1s–4s)
NETWORK_RETRY = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=8.0)

#: Patient retry for Playwright/browser automation (5 attempts, 2s–30s)
BROWSER_RETRY = RetryConfig(max_attempts=5, base_delay=2.0, max_delay=30.0)

#: Gentle retry for external APIs with rate limits (4 attempts, 5s–60s)
API_RETRY = RetryConfig(max_attempts=4, base_delay=5.0, max_delay=60.0)

#: Single retry — fail fast, just one more try
ONE_RETRY = RetryConfig(max_attempts=2, base_delay=1.0)
