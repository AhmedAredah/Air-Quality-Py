"""air_quality.logging

Structured logging helper for the air_quality library.

Provides `get_logger(name: str, **context)` which returns a LoggerAdapter
pre-configured with:
- ISO8601 timestamps
- level name
- logger name
- message
- serialized context (sorted keys) under the `context` record attribute

Design notes:
- Avoid duplicate handlers: only add a handler if none exist.
- Do not propagate to root to prevent double emission via root handlers.
- Use lazy string formatting by passing args to logger methods.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict


_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s | ctx=%(context)s"


class _ContextAdapter(logging.LoggerAdapter):
    """LoggerAdapter that injects a serialized `context` attribute into records."""

    def __init__(
        self, logger: logging.Logger, context: Dict[str, Any] | None = None
    ) -> None:
        serialized = json.dumps(context or {}, sort_keys=True, separators=(",", ":"))
        super().__init__(logger, extra={"context": serialized})

    def process(self, msg, kwargs):
        # Ensure `extra` dict exists and has our context merged (without overriding explicit extra)
        extra = kwargs.get("extra") or {}
        # Preserve any explicit context override by the caller
        if "context" not in extra:
            extra["context"] = self.extra.get("context", "{}")
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    """Return a structured logger with optional bound context.

    Parameters
    ----------
    name: str
        Logger name (e.g., module path). Use package-qualified names for clarity.
    **context: Any
        Key-value pairs to bind as structured context.

    Returns
    -------
    logging.LoggerAdapter
        A logger adapter that injects `context` into log records.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Prevent double logging via root
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        # Consistent formatter with ISO time
        formatter = logging.Formatter(
            fmt=_DEFAULT_FORMAT,
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return _ContextAdapter(logger, context)
