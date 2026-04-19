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
from typing import Any, Callable

from .._http import HttpClient


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
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify a webhook signature from an incoming request.

        Use this in your webhook handler to validate authenticity.

        Args:
            payload: The raw request body as a string.
            signature: The ``X-FlexOps-Signature`` header value (hex-encoded).
            secret: Your webhook signing secret.

        Returns:
            ``True`` if the signature is valid, ``False`` otherwise.
        """
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
