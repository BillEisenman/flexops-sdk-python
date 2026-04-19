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


class InsuranceResource:
    """Shipping insurance quoting, purchasing, and claims."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        return f"/api/workspaces/{ws_id}/insurance/{suffix}"

    def get_providers(self) -> dict[str, Any]:
        """Get available insurance providers for this workspace."""
        return self._http.get(self._ws_path("providers"))

    def get_quote(self, *, carrier: str, declared_value: float, provider: str | None = None) -> dict[str, Any]:
        """Get an insurance quote."""
        body: dict[str, Any] = {"carrier": carrier, "declaredValue": declared_value}
        if provider:
            body["provider"] = provider
        return self._http.post(self._ws_path("quote"), body)

    def purchase(
        self,
        *,
        tracking_number: str,
        carrier: str,
        declared_value: float,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Purchase insurance for a shipment."""
        body: dict[str, Any] = {
            "trackingNumber": tracking_number,
            "carrier": carrier,
            "declaredValue": declared_value,
        }
        if provider:
            body["provider"] = provider
        return self._http.post(self._ws_path("purchase"), body)

    def void(self, policy_id: str) -> dict[str, Any]:
        """Void an insurance policy."""
        return self._http.delete(self._ws_path(f"policies/{policy_id}"))

    def file_claim(self, policy_id: str, *, description: str, claim_amount: float) -> dict[str, Any]:
        """File an insurance claim."""
        return self._http.post(
            self._ws_path(f"policies/{policy_id}/claims"),
            {"description": description, "claimAmount": claim_amount},
        )
