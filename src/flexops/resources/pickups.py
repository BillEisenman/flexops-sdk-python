# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Callable

from .._http import HttpClient


class PickupsResource:
    """Carrier pickup scheduling and management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/pickups"
        return f"{base}/{suffix}" if suffix else base

    def schedule(self, request: dict[str, Any]) -> dict[str, Any]:
        """Schedule a carrier pickup."""
        return self._http.post(self._ws_path(), request)

    def list(self) -> dict[str, Any]:
        """List scheduled pickups."""
        return self._http.get(self._ws_path())

    def get(self, pickup_id: str) -> dict[str, Any]:
        """Get pickup details."""
        return self._http.get(self._ws_path(pickup_id))

    def cancel(self, pickup_id: str) -> dict[str, Any]:
        """Cancel a scheduled pickup."""
        return self._http.delete(self._ws_path(pickup_id))
