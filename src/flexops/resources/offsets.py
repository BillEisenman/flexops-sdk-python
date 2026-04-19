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


class OffsetsResource:
    """Carbon offset operations for shipping labels."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        return f"/api/workspaces/{ws_id}/{suffix}"

    def offset(self, label_id: str) -> dict[str, Any]:
        """Purchase a carbon offset for an existing shipping label."""
        return self._http.post(self._ws_path(f"shipping/labels/{label_id}/offset"))

    def get_emissions(self, label_id: str) -> dict[str, Any]:
        """Get estimated CO2 emissions for a shipping label."""
        return self._http.get(self._ws_path(f"shipping/labels/{label_id}/emissions"))

    def batch_offset(self, label_ids: list[str]) -> dict[str, Any]:
        """Purchase carbon offsets for multiple shipping labels in a single request."""
        return self._http.post(
            self._ws_path("shipping/labels/offset/batch"),
            {"labelIds": label_ids},
        )
