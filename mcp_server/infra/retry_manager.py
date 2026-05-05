from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from mcp_server.config import MCPSettings

P = ParamSpec("P")
T = TypeVar("T")


class RetryableIntegrationError(RuntimeError):
    """Provider error that can be retried safely."""


def async_retry(settings: MCPSettings) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None
            retryable_errors = aiohttp_error() + (RetryableIntegrationError,)
            for attempt in range(1, settings.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_errors as error:
                    last_error = error
                    if attempt == settings.max_retries:
                        break
                    await asyncio.sleep(settings.retry_backoff_seconds * attempt)
            raise RuntimeError(f"{func.__name__} failed after {settings.max_retries} attempts: {last_error}") from last_error

        return wrapper

    return decorator


def aiohttp_error() -> tuple[type[Exception], ...]:
    try:
        import aiohttp

        return (aiohttp.ClientError, asyncio.TimeoutError)
    except Exception:
        return (asyncio.TimeoutError,)
