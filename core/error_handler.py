# core/error_handler.py
"""
Error Handler - Phase 1
Centralized error handling, retry logic, and user-friendly error responses.
Async-compatible.
"""

import asyncio
import logging
import traceback
import functools
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional, Any, Awaitable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

class ErrorCategory(Enum):
    NETWORK          = "network"          # API calls, internet issues
    AUTHENTICATION   = "authentication"   # Token expired, bad credentials
    AUDIO            = "audio"            # Mic, TTS, STT failures
    AGENT            = "agent"            # Agent processing error
    INTENT           = "intent"           # Could not route intent
    TIMEOUT          = "timeout"          # Operation timed out
    UNKNOWN          = "unknown"


@dataclass
class ErrorResult:
    category: ErrorCategory
    original_exception: Exception
    user_message: str                     # What to speak/show to the user
    should_retry: bool
    retry_count: int = 0
    context: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# User-facing messages (keep them short for TTS)
# ---------------------------------------------------------------------------

_USER_MESSAGES: dict[ErrorCategory, str] = {
    ErrorCategory.NETWORK:        "I'm having trouble reaching the internet. Please check your connection.",
    ErrorCategory.AUTHENTICATION: "Authentication failed. Please re-run the setup for that service.",
    ErrorCategory.AUDIO:          "There was an audio issue. Please check your microphone and speakers.",
    ErrorCategory.AGENT:          "Something went wrong while processing your request. Please try again.",
    ErrorCategory.INTENT:         "I didn't understand that. Could you rephrase?",
    ErrorCategory.TIMEOUT:        "That took too long. Please try again.",
    ErrorCategory.UNKNOWN:        "An unexpected error occurred. Please try again.",
}

# Which categories are worth retrying automatically
_RETRYABLE: set[ErrorCategory] = {
    ErrorCategory.NETWORK,
    ErrorCategory.TIMEOUT,
    ErrorCategory.AGENT,
}


# ---------------------------------------------------------------------------
# Exception → ErrorCategory mapping
# ---------------------------------------------------------------------------

def _classify(exc: Exception) -> ErrorCategory:
    name = type(exc).__name__.lower()
    msg  = str(exc).lower()

    if isinstance(exc, asyncio.TimeoutError) or "timeout" in msg:
        return ErrorCategory.TIMEOUT

    if any(k in name for k in ("connection", "network", "http", "url", "socket")):
        return ErrorCategory.NETWORK

    if any(k in msg for k in ("401", "403", "unauthorized", "forbidden",
                               "token", "credential", "auth")):
        return ErrorCategory.AUTHENTICATION

    if any(k in name for k in ("audio", "sounddevice", "pyaudio", "tts", "whisper")):
        return ErrorCategory.AUDIO

    if "intent" in msg or "route" in msg:
        return ErrorCategory.INTENT

    return ErrorCategory.UNKNOWN


# ---------------------------------------------------------------------------
# Core ErrorHandler class
# ---------------------------------------------------------------------------

class ErrorHandler:
    """
    Usage (sync):
        handler = ErrorHandler()
        result = handler.handle(exc, context={"agent": "gmail"})

    Usage (async with retry):
        result = await handler.run_with_retry(my_async_fn, arg1, arg2)

    Decorator:
        @handler.async_safe(default_return="Sorry, failed.")
        async def my_fn(...): ...
    """

    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 1.0,     # seconds between retries
        on_error: Optional[Callable[[ErrorResult], None]] = None,
    ):
        self.max_retries  = max_retries
        self.retry_delay  = retry_delay
        self._on_error_cb = on_error   # optional external callback (e.g. speak error)

    # ------------------------------------------------------------------
    # Public: classify and build ErrorResult
    # ------------------------------------------------------------------

    def handle(
        self,
        exc: Exception,
        context: Optional[dict] = None,
        retry_count: int = 0,
    ) -> ErrorResult:
        category = _classify(exc)
        user_msg = _USER_MESSAGES.get(category, _USER_MESSAGES[ErrorCategory.UNKNOWN])

        result = ErrorResult(
            category=category,
            original_exception=exc,
            user_message=user_msg,
            should_retry=(category in _RETRYABLE and retry_count < self.max_retries),
            retry_count=retry_count,
            context=context or {},
        )

        self._log(result)

        if self._on_error_cb:
            try:
                self._on_error_cb(result)
            except Exception:
                pass  # Never let the callback crash the handler

        return result

    # ------------------------------------------------------------------
    # Public: async retry wrapper
    # ------------------------------------------------------------------

    async def run_with_retry(
        self,
        coro_fn: Callable[..., Awaitable[Any]],
        *args,
        context: Optional[dict] = None,
        **kwargs,
    ) -> tuple[Any, Optional[ErrorResult]]:
        """
        Runs an async function with automatic retry on retryable errors.

        Returns:
            (result, None)             on success
            (None,  ErrorResult)       after all retries exhausted
        """
        last_error: Optional[ErrorResult] = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await coro_fn(*args, **kwargs)
                return result, None

            except Exception as exc:
                error = self.handle(exc, context=context, retry_count=attempt)
                last_error = error

                if error.should_retry:
                    wait = self.retry_delay * (attempt + 1)  # linear backoff
                    logger.info(
                        "Retry %d/%d for %s in %.1fs...",
                        attempt + 1, self.max_retries, getattr(coro_fn, "__name__", "?"), wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    break   # non-retryable, give up immediately

        return None, last_error

    # ------------------------------------------------------------------
    # Public: decorator
    # ------------------------------------------------------------------

    def async_safe(
        self,
        default_return: Any = None,
        context: Optional[dict] = None,
    ):
        """
        Decorator that wraps an async function so it never raises.
        On error, logs + returns default_return.

        @handler.async_safe(default_return="Error occurred.")
        async def risky_fn(x): ...
        """
        def decorator(fn: Callable[..., Awaitable[Any]]):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    self.handle(exc, context=context)
                    return default_return
            return wrapper
        return decorator

    def sync_safe(
        self,
        default_return: Any = None,
        context: Optional[dict] = None,
    ):
        """Same as async_safe but for synchronous functions."""
        def decorator(fn: Callable):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    self.handle(exc, context=context)
                    return default_return
            return wrapper
        return decorator

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log(self, result: ErrorResult) -> None:
        tb = traceback.format_exception(
            type(result.original_exception),
            result.original_exception,
            result.original_exception.__traceback__,
        )
        logger.error(
            "[%s] %s | retry=%d | ctx=%s\n%s",
            result.category.value,
            result.original_exception,
            result.retry_count,
            result.context,
            "".join(tb).strip(),
        )