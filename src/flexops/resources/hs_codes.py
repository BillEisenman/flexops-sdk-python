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


class HsCodesResource:
    """HS code lookup and landed cost estimation for international shipments."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        return f"/api/workspaces/{ws_id}/{suffix}"

    def search(
        self,
        query: str,
        *,
        destination_country: str | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """Search for HS codes by keyword or product description."""
        params: dict[str, Any] = {"query": query, "maxResults": max_results}
        if destination_country is not None:
            params["destinationCountry"] = destination_country
        return self._http.get(self._ws_path("shipping/hs-codes/search"), params)

    def lookup(self, code: str) -> dict[str, Any]:
        """Look up details for a specific HS code."""
        return self._http.get(self._ws_path(f"shipping/hs-codes/{code}"))

    def estimate_landed_cost(self, request: dict[str, Any]) -> dict[str, Any]:
        """Estimate duties, taxes, and fees (landed cost) for an international shipment."""
        return self._http.post(self._ws_path("shipping/landed-cost"), request)
