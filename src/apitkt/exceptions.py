from __future__ import annotations

from typing import Any, Optional


class APIError(Exception):
    """Base exception for apitkt-related errors."""


class APIRequestError(APIError):
    """Errors raised before receiving a response (network issues, timeouts, etc.)."""

    def __init__(self, message: str, original_exception: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class APIResponseError(APIError):
    """Errors raised when a non-success HTTP response is returned."""

    def __init__(
        self,
        status_code: int,
        message: str = "",
        url: str | None = None,
        body: Any | None = None,
    ) -> None:
        super().__init__(message or f"HTTP {status_code} error")
        self.status_code = status_code
        self.url = url
        self.body = body

    def __str__(self) -> str:
        base = super().__str__()
        if self.url:
            base += f" (url={self.url})"
        return base