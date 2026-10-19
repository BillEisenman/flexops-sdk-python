# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-10-19
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Callable

from .._http import HttpClient


class RecurringShipmentsResource:
    """Recurring shipment schedules: each run ships the preset's package to the schedule's address.

    Reads work with any API key or a user token. Writes need a user token (``auth.login``) or an API
    key granted the ``recurring-shipments:write`` scope; a key without it gets 403 ``API_KEY_SCOPE_REQUIRED``
    naming ``requiredScopes``.

    Responses are bare JSON, not the ``{"success", "data"}`` envelope. ``interval`` is a
    ``RecurrenceInterval`` number; ``CUSTOM`` uses ``cronExpression``.
    """

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/recurring-shipments"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> list[dict[str, Any]]:
        """List the workspace's recurring shipments."""
        return self._http.get(self._ws_path())

    def get(self, id: str) -> dict[str, Any]:
        """Get a recurring shipment. A missing one is 404."""
        return self._http.get(self._ws_path(id))

    def create(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create a recurring shipment (201).

        ``request`` is the Gateway ``CreateRecurringShipmentRequest``: ``name`` and ``firstRunUtc``
        (ISO 8601) are required; ``interval`` (``RecurrenceInterval``), ``presetId``, ``addressId``,
        ``cronExpression`` and ``maxFailures`` (1-100, default 3) are optional. A run needs an
        ``addressId``; the preset supplies the package and service.
        """
        return self._http.post(self._ws_path(), request)

    def update(self, id: str, request: dict[str, Any]) -> dict[str, Any]:
        """Update a recurring shipment.

        Every field is optional: ``name``, ``presetId``, ``addressId``, ``interval``,
        ``cronExpression``, ``maxFailures``.
        """
        return self._http.put(self._ws_path(id), request)

    def delete(self, id: str) -> None:
        """Delete a recurring shipment (204)."""
        return self._http.delete(self._ws_path(id))

    def pause(self, id: str) -> None:
        """Pause a recurring shipment (204)."""
        return self._http.post(self._ws_path(f"{id}/pause"))

    def resume(self, id: str) -> None:
        """Resume a paused recurring shipment (204)."""
        return self._http.post(self._ws_path(f"{id}/resume"))

    def trigger(self, id: str, *, idempotency_key: str | None = None) -> None:
        """Run a recurring shipment now, creating an order (204).

        The Gateway refuses this when it cannot check the ``Idempotency-Key``. Pass an
        ``idempotency_key`` you persist with the run to keep a later retry from creating a second
        order; without one the SDK generates a key per call.
        """
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return self._http.post(self._ws_path(f"{id}/trigger"), headers=headers)
