"""Exceptions for the Data Legion API client."""

from __future__ import annotations

from typing import Any


class DataLegionError(Exception):
    """Base exception for all Data Legion API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error: str | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error
        self.details = details

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"error={self.error!r})"
        )


class AuthenticationError(DataLegionError):
    """Raised when the API key is invalid or missing (HTTP 401)."""


class InsufficientCreditsError(DataLegionError):
    """Raised when the account has insufficient credits (HTTP 402)."""


class ValidationError(DataLegionError):
    """Raised when the request fails validation (HTTP 422)."""


class RateLimitError(DataLegionError):
    """Raised when the rate limit is exceeded (HTTP 429)."""


class APIError(DataLegionError):
    """Raised for any error status without a more specific class below or above.

    The classes below subclass it, so ``except APIError`` still catches every
    status it caught before they existed.
    """


class BadRequestError(APIError):
    """Raised when the request is malformed, e.g. an unknown field name (HTTP 400)."""


class PermissionDeniedError(APIError):
    """Raised when the key or its contract doesn't cover the endpoint (HTTP 403)."""


class NotFoundError(APIError):
    """Raised when nothing matches, e.g. an enrich with no match (HTTP 404). No credits are used."""


class RequestTimeoutError(APIError):
    """Raised when a search runs past the API's time limit (HTTP 408). Narrow the query or retry."""


class ServerError(APIError):
    """Raised for server and gateway errors (HTTP 5xx). Safe to retry with backoff."""
