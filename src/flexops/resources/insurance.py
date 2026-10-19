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

    def get_quote(
        self,
        *,
        carrier_code: str,
        declared_value: float,
        tracking_number: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Get an insurance quote."""
        body: dict[str, Any] = {"declaredValue": declared_value, "carrierCode": carrier_code}
        if tracking_number is not None:
            body["trackingNumber"] = tracking_number
        if provider is not None:
            body["provider"] = provider
        return self._http.post(self._ws_path("quote"), body)

    def purchase(
        self,
        *,
        tracking_number: str,
        carrier_code: str,
        declared_value: float,
        coverage_tier: str | None = None,
        provider: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Purchase insurance for a shipment. The premium is charged to the workspace wallet.

        Pass an ``idempotency_key`` you persist with the purchase to keep a retry after an uncertain
        outcome from buying a second policy; without one the SDK generates a key per call.
        """
        body: dict[str, Any] = {
            "trackingNumber": tracking_number,
            "carrierCode": carrier_code,
            "declaredValue": declared_value,
        }
        if coverage_tier is not None:
            body["coverageTier"] = coverage_tier
        if provider is not None:
            body["provider"] = provider
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return self._http.post(self._ws_path("policies"), body, headers=headers)

    def void(self, policy_id: str) -> dict[str, Any]:
        """Void an insurance policy."""
        return self._http.delete(self._ws_path(f"policies/{policy_id}"))

    def file_claim(
        self,
        policy_id: str,
        *,
        claim_reason: str,
        claim_amount: float,
        evidence_json: str | None = None,
    ) -> dict[str, Any]:
        """File a claim against a policy."""
        body: dict[str, Any] = {"policyId": policy_id, "claimReason": claim_reason, "claimAmount": claim_amount}
        if evidence_json is not None:
            body["evidenceJson"] = evidence_json
        return self._http.post(self._ws_path("claims"), body)
