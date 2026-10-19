# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any

from .._http import HttpClient


class InventoryResource:
    """Inventory reads via the legacy VisionSuite API proxy (read-only: the proxy refuses API-key writes)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_warehouse_snapshot(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get a warehouse inventory snapshot."""
        return self._http.get("/api/ApiProxy/api/v1/Inventory/getWarehouseInventorySnapshot", params)

    def get_complete_snapshot(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get a complete inventory snapshot across all warehouses."""
        return self._http.get("/api/ApiProxy/api/v1/Inventory/getCompleteInventorySnapshot", params)

    def get_part_numbers(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the list of all part numbers."""
        return self._http.get("/api/ApiProxy/api/v1/Inventory/getPartNumberList", params)
