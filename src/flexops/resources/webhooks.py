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
from typing import Any, Callable, Iterable

from .._http import HttpClient
from .._types import WebhookEventType

DEFAULT_SIGNATURE_TOLERANCE_SECONDS = 300
"""Default maximum age, in seconds, of ``X-FlexOps-Timestamp`` accepted by ``verify_signature``."""

_SIGNATURE_PREFIX = "sha256="
_TIMESTAMP_RE = re.compile(r"[0-9]+")
_HEX_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
_KNOWN_EVENTS = tuple(event.value for event in WebhookEventType)


def _to_event_types(events: Iterable[WebhookEventType | str]) -> str:
    """Joins event names into the Gateway's comma-separated ``eventTypes``.

    The Gateway ignores an ``events`` field (subscribing to every event) and matches each name
    exactly, so a name it never sends would leave the subscription silent; it is refused here.
    """
    if isinstance(events, str):
        raise TypeError("events must be a list of event names, not a single string.")
    names: list[str] = []
    for event in events:
        name = event.value if isinstance(event, WebhookEventType) else event
        if name not in names:
            names.append(name)
    if not names:
        raise ValueError("events must name at least one event; leave it out to receive every event.")
    unknown = [name for name in names if name not in _KNOWN_EVENTS]
    if unknown:
        raise ValueError(
            f"Unknown webhook event: {', '.join(map(str, unknown))}. FlexOps sends {', '.join(_KNOWN_EVENTS)}."
        )
    return ",".join(names)


def _to_envelope(body: Any) -> dict[str, Any]:
    """Wraps the bare subscription the Gateway returns from create.

    Create answers ``201`` with the subscription itself, not the ``{"success", "data"}`` envelope
    the other webhook routes use. A bare body is wrapped so ``data["secret"]`` holds the signing
    secret; an envelope passes through unchanged.
    """
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body
    return {"success": True, "data": body}


class WebhooksResource:
    """Webhook subscription management and signature verification.

    Every method that calls the Gateway needs a signed-in user's access token (``access_token=``,
    ``set_access_token()`` or ``auth.login()``). The Gateway refuses API keys on every webhook route,
    reads included, with 403 ``SIGNED_IN_USER_REQUIRED`` (a ``FlexOpsError`` with that ``code``),
    whatever the key's scopes. Reads are refused too because webhook delivery logs carry each
    delivery's payload (order and customer data). A client with an API key sends the key even when an
    access token is also set, so call these methods from a client created without ``api_key``.
    ``verify_signature`` makes no request and needs no credentials.
    """

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
        """List all webhook subscriptions for the workspace.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``). Reads are signed-in only, like the writes, because webhook delivery logs
        carry each delivery's payload (order and customer data).

        Raises:
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        return self._http.get(self._ws_path())

    def create(
        self,
        url: str,
        events: Iterable[WebhookEventType | str] | None = None,
        *,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a webhook subscription.

        ``events`` lists the ``WebhookEventType`` names to receive; leave it out to receive every
        event. It is sent as the Gateway's comma-separated ``eventTypes``.

        Returns ``{"success": True, "data": <subscription>}``; ``result["data"]["secret"]`` is the
        signing secret, returned only here.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``).

        Raises:
            ValueError: ``events`` is empty or names an event FlexOps never sends.
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        body: dict[str, Any] = {"url": url}
        if description is not None:
            body["description"] = description
        if events is not None:
            body["eventTypes"] = _to_event_types(events)
        return _to_envelope(self._http.post(self._ws_path(), body))

    def update(self, webhook_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a webhook subscription.

        ``data`` takes ``url``, ``description``, ``status`` (``Active``, ``Paused`` or ``Disabled``)
        and ``events``, a list of ``WebhookEventType`` names that replaces the subscribed events
        and is sent as ``eventTypes``.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``).

        Raises:
            ValueError: ``events`` is empty or names an event FlexOps never sends.
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        body = dict(data)
        if "events" in body:
            body["eventTypes"] = _to_event_types(body.pop("events"))
        return self._http.put(self._ws_path(webhook_id), body)

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook subscription. The Gateway answers 204 No Content, so this returns ``None``.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``).

        Raises:
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        return self._http.delete(self._ws_path(webhook_id))

    def rotate_secret(self, webhook_id: str) -> dict[str, Any]:
        """Rotate the signing secret for a webhook.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``).

        Raises:
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        return self._http.post(self._ws_path(f"{webhook_id}/rotate-secret"))

    def list_delivery_logs(self, webhook_id: str) -> dict[str, Any]:
        """List delivery logs for a webhook.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``). Reads are signed-in only, like the writes, because webhook delivery logs
        carry each delivery's payload (order and customer data).

        Raises:
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        return self._http.get(self._ws_path(f"{webhook_id}/deliveries"))

    def test(self, webhook_id: str) -> dict[str, Any]:
        """Send a test event (``X-FlexOps-Event: test``) to a webhook. Needs the Owner or Admin role.

        Needs a signed-in user's access token (``access_token=``, ``set_access_token()`` or
        ``auth.login()``).

        Raises:
            FlexOpsError: ``status`` 403 with ``code`` ``SIGNED_IN_USER_REQUIRED`` when the client
                authenticates with an API key.
        """
        return self._http.post(self._ws_path(f"{webhook_id}/test"))

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
