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


class ScanFormsResource:
    """USPS scan form (SCAN/manifest) management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/scan-forms"
        return f"{base}/{suffix}" if suffix else base

    def create(self, tracking_numbers: list[str]) -> dict[str, Any]:
        """Create a USPS scan form (SCAN/manifest)."""
        return self._http.post(self._ws_path(), {"trackingNumbers": tracking_numbers})

    def list(self) -> dict[str, Any]:
        """List scan forms."""
        return self._http.get(self._ws_path())

    def get(self, scan_form_id: str) -> dict[str, Any]:
        """Get a scan form by ID."""
        return self._http.get(self._ws_path(scan_form_id))
