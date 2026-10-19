# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import quote

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
        """Schedule a carrier pickup.

        ``request`` is the Gateway ``SchedulePickupRequest``: ``carrierCode``, ``pickupDate``,
        ``street``, ``city``, ``state``, ``postalCode`` and ``packageCount``, plus optional ``country``
        (default ``US``), ``totalWeightOz``, ``specialInstructions``, ``readyTime``, ``closeTime``,
        ``contactName`` and ``contactPhone``.
        """
        return self._http.post(self._ws_path(), request)

    def list(self) -> dict[str, Any]:
        """List the workspace's scheduled pickups, most recent first."""
        return self._http.get(self._ws_path("scheduled"))

    def get(self, pickup_id: str, *, carrier_code: str | None = None) -> dict[str, Any]:
        """Get pickup details. ``carrier_code`` defaults to ``usps`` on the Gateway."""
        return self._http.get(self._ws_path(pickup_id), _carrier_query(carrier_code))

    def cancel(self, pickup_id: str, *, carrier_code: str | None = None) -> dict[str, Any]:
        """Cancel a scheduled pickup. ``carrier_code`` defaults to ``usps`` on the Gateway."""
        query = _carrier_query(carrier_code)
        suffix = f"{pickup_id}?carrierCode={quote(carrier_code, safe='')}" if query else pickup_id
        return self._http.delete(self._ws_path(suffix))


def _carrier_query(carrier_code: str | None) -> dict[str, Any] | None:
    return {"carrierCode": carrier_code} if carrier_code else None
