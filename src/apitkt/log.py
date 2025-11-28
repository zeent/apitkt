from __future__ import annotations

import logging
import time
from typing import Any, Mapping, Optional

import httpx

from .client import APIClient

logger = logging.getLogger("apitkt.log")


SENSITIVE_HEADER_KEYS = {"authorization", "proxy-authorization"}
SENSITIVE_JSON_KEYS = {"password", "token", "access_token", "refresh_token", "secret"}


def _redact_mapping(data: Mapping[str, Any], sensitive_keys: set[str]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            redacted[key] = "***redacted***"
        else:
            redacted[key] = value
    return redacted


class LoggedClient(APIClient):
    """
    An APIClient that logs requests and responses.

    It logs:
    - method, path, status code
    - elapsed time in ms
    - optionally request/response metadata (without sensitive values)
    """

    def __init__(
        self,
        *args: Any,
        log_headers: bool = True,
        log_body_preview: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.log_headers = log_headers
        self.log_body_preview = log_body_preview

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
        start = time.perf_counter()
        try:
            response = super().request(
                method,
                path,
                params=params,
                headers=headers,
                json=json,
                data=data,
                **kwargs,
            )
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0

        extra: dict[str, Any] = {
            "method": method.upper(),
            "path": path,
            "elapsed_ms": round(elapsed_ms, 2),
        }

        if params:
            extra["params"] = dict(params)

        if self.log_headers:
            # Headers from the underlying client and the request-specific ones
            combined_headers = {}
            combined_headers.update(dict(self._client.headers))
            if headers:
                combined_headers.update(dict(headers))
            extra["request_headers"] = _redact_mapping(
                combined_headers,
                SENSITIVE_HEADER_KEYS,
            )

        if self.log_body_preview and json is not None:
            # Redact common sensitive fields in JSON payloads
            if isinstance(json, dict):
                extra["request_json"] = _redact_mapping(json, SENSITIVE_JSON_KEYS)
            else:
                extra["request_json"] = "<non-dict json payload>"

        if self.log_body_preview:
            try:
                content_type = response.headers.get("content-type", "")
                extra["response_content_type"] = content_type
                if "application/json" in content_type.lower():
                    body = response.json()
                    if isinstance(body, dict):
                        extra["response_json_preview"] = {
                            k: body[k] for k in list(body.keys())[:10]
                        }
                    else:
                        extra["response_json_preview"] = "<non-dict json payload>"
                else:
                    text = response.text
                    extra["response_text_preview"] = text[:200] + ("..." if len(text) > 200 else "")
            except Exception:
                extra["response_preview_error"] = "could not read response body"

        extra["status_code"] = response.status_code

        logger.info("api_call", extra=extra)
        return response