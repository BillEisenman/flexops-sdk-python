# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

import hashlib
import hmac
import re
import time
from typing import Any, Callable

from .._http import HttpClient

DEFAULT_SIGNATURE_TOLERANCE_SECONDS = 300
"""Default maximum age, in seconds, of ``X-FlexOps-Timestamp`` accepted by ``verify_signature``."""

_SIGNATURE_PREFIX = "sha256="
_TIMESTAMP_RE = re.compile(r"[0-9]+")
_HEX_DIGEST_RE = re.compile(r"[0-9a-f]{64}")


class WebhooksResource:
    """Webhook subscription management and signature verification."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/webhooks"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> dict[str, Any]:
        """List all webhook subscriptions for the workspace."""
        return self._http.get(self._ws_path())

    def get(self, webhook_id: str) -> dict[str, Any]:
        """Get a webhook subscription by ID."""
        return self._http.get(self._ws_path(webhook_id))

    def create(self, url: str, events: list[str]) -> dict[str, Any]:
        """Create a webhook subscription."""
        return self._http.post(self._ws_path(), {"url": url, "events": events})

    def update(self, webhook_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a webhook subscription."""
        return self._http.put(self._ws_path(webhook_id), data)

    def delete(self, webhook_id: str) -> dict[str, Any]:
        """Delete a webhook subscription."""
        return self._http.delete(self._ws_path(webhook_id))

    def rotate_secret(self, webhook_id: str) -> dict[str, Any]:
        """Rotate the signing secret for a webhook."""
        return self._http.post(self._ws_path(f"{webhook_id}/rotate-secret"))

    def list_delivery_logs(self, webhook_id: str) -> dict[str, Any]:
        """List delivery logs for a webhook."""
        return self._http.get(self._ws_path(f"{webhook_id}/deliveries"))

    @staticmethod
    def verify_signature(
        payload: str | bytes | bytearray,
        signature: str | None,
        secret: str,
        *,
        timestamp: str | None,
        tolerance: float = DEFAULT_SIGNATURE_TOLERANCE_SECONDS,
        now: float | None = None,
    ) -> bool:
        """Verify that an incoming request is a genuine FlexOps webhook delivery.

        FlexOps signs ``{X-FlexOps-Timestamp}.{raw body}`` with HMAC-SHA256, keyed with the
        subscription secret (the whole ``whsec_...`` string), and sends
        ``X-FlexOps-Signature: sha256=<lowercase hex>``.

        Args:
            payload: The raw request body exactly as received, as bytes or a string. Do not pass
                re-serialized JSON; it will not reproduce the signed bytes.
            signature: The ``X-FlexOps-Signature`` header. ``sha256=<hex>`` and bare ``<hex>``
                are accepted.
            secret: Your webhook signing secret.
            timestamp: The ``X-FlexOps-Timestamp`` header (Unix seconds). Keyword-only and required.
            tolerance: Maximum distance in seconds between ``timestamp`` and now, in either
                direction. Defaults to 300.
            now: The current time in Unix seconds. Defaults to ``time.time()``; set it in tests.

        Returns:
            ``True`` only when the signature matches and the timestamp is within tolerance.
            A missing, malformed or wrong-length signature, or a missing, non-numeric or
            out-of-tolerance timestamp, returns ``False``.

        Raises:
            ValueError: If ``secret`` is empty or ``tolerance`` is negative.
            TypeError: If ``payload`` is not bytes or a string.
        """
        if not isinstance(secret, str) or not secret:
            raise ValueError("A webhook signing secret is required.")
        if isinstance(payload, str):
            body = payload.encode("utf-8")
        elif isinstance(payload, (bytes, bytearray)):
            body = bytes(payload)
        else:
            raise TypeError("payload must be the raw request body as bytes or a string.")
        if not tolerance >= 0:
            raise ValueError("tolerance must be a non-negative number of seconds.")

        if not isinstance(signature, str) or not isinstance(timestamp, str):
            return False

        ts = timestamp.strip()
        if not _TIMESTAMP_RE.fullmatch(ts):
            return False
        current = time.time() if now is None else now
        # Compares int with float exactly (no overflow on huge values); a NaN clock fails closed.
        if not (current - tolerance <= int(ts) <= current + tolerance):
            return False

        provided = signature.strip()
        if provided[: len(_SIGNATURE_PREFIX)].lower() == _SIGNATURE_PREFIX:
            provided = provided[len(_SIGNATURE_PREFIX) :]
        provided = provided.lower()
        if not _HEX_DIGEST_RE.fullmatch(provided):
            return False

        expected = hmac.new(secret.encode("utf-8"), ts.encode("ascii") + b"." + body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(provided.encode("ascii"), expected.encode("ascii"))
