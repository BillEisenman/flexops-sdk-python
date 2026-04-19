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


class ReportsResource:
    """Scheduled report management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/report-schedules"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> dict[str, Any]:
        """List all scheduled reports."""
        return self._http.get(self._ws_path())

    def get(self, id: str) -> dict[str, Any]:
        """Get a scheduled report by ID."""
        return self._http.get(self._ws_path(id))

    def create(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create a new scheduled report."""
        return self._http.post(self._ws_path(), request)

    def update(self, id: str, request: dict[str, Any]) -> dict[str, Any]:
        """Update an existing scheduled report."""
        return self._http.put(self._ws_path(id), request)

    def delete(self, id: str) -> dict[str, Any]:
        """Delete a scheduled report."""
        return self._http.delete(self._ws_path(id))
