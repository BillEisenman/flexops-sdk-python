# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-31
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Callable

from .._http import HttpClient


class RecurringShipmentsResource:
    """Recurring shipment schedule management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/recurring-shipments"
        return f"{base}/{suffix}" if suffix else base

    def list(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any]:
        """List all recurring shipment schedules."""
        query: dict[str, Any] = {}
        if page is not None:
            query["page"] = page
        if page_size is not None:
            query["pageSize"] = page_size
        if is_active is not None:
            query["isActive"] = is_active
        return self._http.get(self._ws_path(), query or None)

    def get(self, id: str) -> dict[str, Any]:
        """Get a recurring shipment schedule by ID."""
        return self._http.get(self._ws_path(id))

    def create(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create a new recurring shipment schedule."""
        return self._http.post(self._ws_path(), request)

    def update(self, id: str, request: dict[str, Any]) -> dict[str, Any]:
        """Update an existing recurring shipment schedule."""
        return self._http.put(self._ws_path(id), request)

    def delete(self, id: str) -> dict[str, Any]:
        """Delete a recurring shipment schedule."""
        return self._http.delete(self._ws_path(id))

    def pause(self, id: str) -> dict[str, Any]:
        """Pause an active recurring shipment schedule."""
        return self._http.post(self._ws_path(f"{id}/pause"))

    def resume(self, id: str) -> dict[str, Any]:
        """Resume a paused recurring shipment schedule."""
        return self._http.post(self._ws_path(f"{id}/resume"))

    def trigger(self, id: str) -> dict[str, Any]:
        """Manually trigger an immediate run of a recurring shipment schedule."""
        return self._http.post(self._ws_path(f"{id}/trigger"))
