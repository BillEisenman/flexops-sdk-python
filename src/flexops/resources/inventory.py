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
    """Inventory management via VisionSuite API proxy."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def post_asn_receipt(self, receipt: Any) -> dict[str, Any]:
        """Post a new ASN (Advance Shipment Notice) receipt."""
        return self._http.post("/api/ApiProxy/api/v1/Inventory/postNewAsnReceipt", receipt)

    def get_warehouse_snapshot(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get a warehouse inventory snapshot."""
        return self._http.get("/api/ApiProxy/api/v1/Inventory/getWarehouseInventorySnapshot", params)

    def get_complete_snapshot(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get a complete inventory snapshot across all warehouses."""
        return self._http.get("/api/ApiProxy/api/v1/Inventory/getCompleteInventorySnapshot", params)

    def get_part_numbers(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the list of all part numbers."""
        return self._http.get("/api/ApiProxy/api/v1/Inventory/getPartNumberList", params)

    def update_inventory(self, data: Any) -> dict[str, Any]:
        """Update customer inventory (V2)."""
        return self._http.post("/api/ApiProxy/api/v2/Inventory/postCustomerInventoryUpdate", data)
