from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, MutableMapping, Optional

import httpx

from .exceptions import APIRequestError, APIResponseError

logger = logging.getLogger(__name__)


class APIClient:
    """
    Simple, extensible HTTP API client built on top of httpx.

    This first version provides:
    - Base URL handling
    - Default headers and auth
    - Simple request helpers (get/post/put/delete)
    - Basic error handling with custom exceptions
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        headers: Optional[Mapping[str, str]] = None,
        auth: Any | None = None,
        raise_for_status: bool = True,
    ) -> None:
        if base_url.endswith("/"):
            base_url = base_url[:-1]

        self.base_url = base_url
        self.timeout = timeout
        self.raise_for_status = raise_for_status

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=dict(headers or {}),
            auth=auth,
        )

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return path

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Any | None = None,
        data: Any | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Perform an HTTP request and return an httpx.Response.

        Raises:
            APIRequestError: for network-related problems.
            APIResponseError: for non-success status codes (if raise_for_status=True).
        """
        url = self._build_url(path)

        merged_headers: MutableMapping[str, str] = {}
        if self._client.headers:
            merged_headers.update(self._client.headers)
        if headers:
            merged_headers.update(headers)

        try:
            response = self._client.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=merged_headers,
                json=json,
                data=data,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise APIRequestError(f"Error while requesting {url}", exc) from exc

        if self.raise_for_status and not (200 <= response.status_code < 300):
            raise APIResponseError(
                status_code=response.status_code,
                url=str(response.url),
                body=_safe_body_preview(response),
            )

        return response

    # Convenience HTTP methods

    def get(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self.request("GET", path, params=params, headers=headers, **kwargs)

    def post(
        self,
        path: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self.request("POST", path, json=json, data=data, headers=headers, **kwargs)

    def put(
        self,
        path: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self.request("PUT", path, json=json, data=data, headers=headers, **kwargs)

    def delete(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self.request("DELETE", path, params=params, headers=headers, **kwargs)

    def close(self) -> None:
        """Close the underlying httpx.Client."""
        self._client.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


def _safe_body_preview(response: httpx.Response, max_len: int = 500) -> Dict[str, Any]:
    """
    Return a small preview of the response body for debugging.

    This is meant to be used in exceptions and logs, not as full content.
    """
    try:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type.lower():
            obj = response.json()
            return {"type": "json", "preview": obj}
        text = response.text
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."
        return {"type": "text", "preview": text}
    except Exception:
        return {"type": "unknown", "preview": None}