"""Shared API error helpers."""

import logging

from fastapi import HTTPException

logger = logging.getLogger("stocksense.upstream")


def provider_error(exc: Exception) -> HTTPException:
    """Log the real upstream failure server-side and return a generic 502 so
    provider internals (library errors, URLs) never reach the client."""
    logger.warning("Market-data provider error: %s", exc)
    return HTTPException(
        status_code=502, detail="Market data provider is unavailable right now."
    )
