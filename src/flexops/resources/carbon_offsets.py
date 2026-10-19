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


class CarbonOffsetsResource:
    """Carbon offsets for shipments. Requires the Pro plan or above."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/carbon-offsets"
        return f"{base}/{suffix}" if suffix else base

    def quote(self, *, weight_lbs: float, distance_miles: float) -> dict[str, Any]:
        """Quote an offset for a shipment without buying it."""
        return self._http.post(self._ws_path("quote"), {"weightLbs": weight_lbs, "distanceMiles": distance_miles})

    def purchase(
        self,
        *,
        tracking_number: str,
        weight_lbs: float,
        distance_miles: float,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Buy an offset for a shipment. The cost is charged to the workspace wallet.

        The Gateway refuses this purchase when it cannot check the ``Idempotency-Key``. Pass an
        ``idempotency_key`` you persist with the purchase to keep a retry after an uncertain outcome
        from buying a second offset; without one the SDK generates a key per call.
        """
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        body = {"trackingNumber": tracking_number, "weightLbs": weight_lbs, "distanceMiles": distance_miles}
        return self._http.post(self._ws_path("purchase"), body, headers=headers)

    def list(self, *, page: int | None = None, page_size: int | None = None) -> dict[str, Any]:
        """List the workspace's offsets, newest first."""
        query: dict[str, Any] = {}
        if page is not None:
            query["page"] = page
        if page_size is not None:
            query["pageSize"] = page_size
        return self._http.get(self._ws_path(), query or None)

    def get(self, offset_id: str) -> dict[str, Any]:
        """Get one offset."""
        return self._http.get(self._ws_path(offset_id))

    def get_summary(self) -> dict[str, Any]:
        """Totals across the workspace's offsets."""
        return self._http.get(self._ws_path("summary"))

    def get_settings(self) -> dict[str, Any]:
        """Get the automatic-offset setting."""
        return self._http.get(self._ws_path("settings"))

    def update_settings(self, *, auto_offset_enabled: bool) -> dict[str, Any]:
        """Turn automatic offsets on or off."""
        return self._http.put(self._ws_path("settings"), {"autoOffsetEnabled": auto_offset_enabled})
