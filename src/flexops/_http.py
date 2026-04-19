# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

import random
import time
from typing import Any

import requests

from ._errors import FlexOpsAuthError, FlexOpsError, FlexOpsRateLimitError
from ._types import FlexOpsConfig, RetryConfig

_DEFAULT_BASE_URL = "https://gateway.flexops.io"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_RETRY = RetryConfig()


class HttpClient:
    """Low-level HTTP client with retry, auth, and connection pooling."""

    def __init__(self, config: FlexOpsConfig) -> None:
        self._base_url = config.base_url.rstrip("/")
        self._timeout = config.timeout
        self._retry = config.retry or _DEFAULT_RETRY
        self._custom_headers = config.headers or {}
        self._access_token = config.access_token
        self._api_key = config.api_key
        self._session = requests.Session()

    def set_access_token(self, token: str) -> None:
        self._access_token = token

    def set_api_key(self, key: str) -> None:
        self._api_key = key

    # -- Convenience methods ------------------------------------------------

    def get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, query=query)

    def post(self, path: str, body: Any = None, query: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, body=body, query=query)

    def put(self, path: str, body: Any = None) -> Any:
        return self.request("PUT", path, body=body)

    def patch(self, path: str, body: Any = None) -> Any:
        return self.request("PATCH", path, body=body)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    # -- Core request -------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        url = self._build_url(path)
        req_headers = self._build_headers(headers)
        effective_timeout = timeout or self._timeout
        params = self._clean_query(query)

        last_error: Exception | None = None

        for attempt in range(self._retry.max_retries + 1):
            if attempt > 0:
                delay = self._calculate_backoff(attempt)
                time.sleep(delay)

            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    json=body if body is not None else None,
                    params=params or None,
                    headers=req_headers,
                    timeout=effective_timeout,
                )

                if resp.ok:
                    content_type = resp.headers.get("content-type", "")
                    if "application/json" in content_type:
                        return resp.json()
                    return resp.content

                # Rate limited
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("retry-after", "0"))
                    last_error = FlexOpsRateLimitError(
                        f"Rate limited. Retry after {retry_after}s",
                        retry_after=retry_after,
                    )
                    if 429 in self._retry.retryable_status_codes:
                        continue
                    raise last_error

                # Auth errors - don't retry
                if resp.status_code == 401:
                    raise FlexOpsAuthError()
                if resp.status_code == 403:
                    raise FlexOpsError(
                        "Access denied. Check your plan tier and feature entitlements.",
                        status=403,
                        code="FORBIDDEN",
                    )

                # Parse error body
                error_body: dict[str, Any] = {}
                try:
                    error_body = resp.json()
                except Exception:
                    pass

                error = FlexOpsError(
                    error_body.get("message", f"HTTP {resp.status_code}: {resp.reason}"),
                    status=resp.status_code,
                    errors=error_body.get("errors"),
                )

                if resp.status_code in self._retry.retryable_status_codes:
                    last_error = error
                    continue

                raise error

            except FlexOpsError:
                raise
            except requests.Timeout:
                last_error = FlexOpsError(
                    f"Request timed out after {effective_timeout}s",
                    status=0,
                    code="TIMEOUT",
                )
                if attempt < self._retry.max_retries:
                    continue
            except requests.RequestException as exc:
                last_error = FlexOpsError(str(exc), status=0, code="CONNECTION_ERROR")
                if attempt < self._retry.max_retries:
                    continue

        raise last_error or FlexOpsError("Request failed after retries", status=0, code="RETRY_EXHAUSTED")

    # -- Helpers ------------------------------------------------------------

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self._base_url}{path}"

    def _build_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._custom_headers,
            **(extra or {}),
        }
        if self._api_key:
            headers["X-Api-Key"] = self._api_key
        elif self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def _calculate_backoff(self, attempt: int) -> float:
        jitter = random.uniform(0.85, 1.15)
        return min(self._retry.base_delay * (2 ** (attempt - 1)) * jitter, 30.0)

    @staticmethod
    def _clean_query(query: dict[str, Any] | None) -> dict[str, str] | None:
        if not query:
            return None
        return {k: str(v) for k, v in query.items() if v is not None}
