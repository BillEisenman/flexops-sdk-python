# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .._http import HttpClient


class HsCodesResource:
    """HS code lookup and landed cost estimation for international shipments.

    These are Gateway ``/api/shipping/...`` routes; they are not workspace-scoped.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def search(
        self,
        query: str,
        *,
        destination_country: str | None = None,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for HS codes by keyword or product description. Returns a bare list."""
        params: dict[str, Any] = {"query": query, "maxResults": max_results}
        if destination_country is not None:
            params["destinationCountry"] = destination_country
        return self._http.get("/api/shipping/hs-codes/search", params)

    def lookup(self, code: str) -> dict[str, Any]:
        """Look up details for a specific HS code. Returns the bare result."""
        return self._http.get(f"/api/shipping/hs-codes/{quote(code, safe='')}")

    def estimate_landed_cost(self, request: dict[str, Any]) -> dict[str, Any]:
        """Estimate duties, taxes and fees (landed cost) for an international shipment.

        ``request`` is the Gateway ``LandedCostRequest``: ``destinationCountry``, ``shippingCost`` and
        ``items``, each ``{description, quantity, value, weightOz, originCountry, hsCode?,
        skuOrProductId?}``. Returns the bare estimate.
        """
        return self._http.post("/api/shipping/landed-cost", request)
