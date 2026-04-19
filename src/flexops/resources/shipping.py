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


class ShippingResource:
    """Normalized shipping operations (rate shopping, labels, tracking)."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        return f"/api/workspaces/{ws_id}/{suffix}"

    # -- Rate Shopping ------------------------------------------------------

    def get_rates(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get shipping rates from all configured carriers."""
        return self._http.post(self._ws_path("shipping/rates"), request)

    def get_cheapest_rate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get the single cheapest rate across all carriers."""
        return self._http.post(self._ws_path("shipping/rates/cheapest"), request)

    def get_fastest_rate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get the single fastest rate across all carriers."""
        return self._http.post(self._ws_path("shipping/rates/fastest"), request)

    # -- Labels -------------------------------------------------------------

    def create_label(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create a shipping label."""
        return self._http.post(self._ws_path("shipping/labels"), request)

    def cancel_label(self, label_id: str) -> dict[str, Any]:
        """Cancel (void) a shipping label."""
        return self._http.delete(self._ws_path(f"shipping/labels/{label_id}"))

    # -- Tracking -----------------------------------------------------------

    def track(self, tracking_number: str) -> dict[str, Any]:
        """Track a shipment by tracking number."""
        return self._http.get(self._ws_path(f"shipping/track/{tracking_number}"))

    # -- Address Validation -------------------------------------------------

    def validate_address(self, address: dict[str, Any]) -> dict[str, Any]:
        """Validate and correct a shipping address."""
        return self._http.post(self._ws_path("shipping/addresses/validate"), address)

    # -- Batch Labels -------------------------------------------------------

    def create_batch(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create labels in batch."""
        return self._http.post(self._ws_path("labels/batch"), request)

    def preview_batch(self, request: dict[str, Any]) -> dict[str, Any]:
        """Preview a batch without purchasing (dry-run)."""
        return self._http.post(self._ws_path("labels/batch/preview"), request)

    def get_batch_status(self, job_id: str) -> dict[str, Any]:
        """Get batch job status."""
        return self._http.get(self._ws_path(f"labels/batch/{job_id}"))

    def download_batch_label(self, job_id: str, item_id: str) -> bytes:
        """Download a label from a batch job."""
        return self._http.get(self._ws_path(f"labels/batch/{job_id}/items/{item_id}/label"))

    # -- Carriers -----------------------------------------------------------

    def get_carriers(self) -> dict[str, Any]:
        """List available carriers and their services."""
        return self._http.get(self._ws_path("shipping/carriers"))

    # -- Recommendations & Predictions --------------------------------------

    def get_recommendations(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get AI-powered shipping service recommendations."""
        return self._http.post(self._ws_path("shipping/recommendations"), request)

    def predict_delivery(self, request: dict[str, Any]) -> dict[str, Any]:
        """Predict the delivery date for a prospective shipment."""
        return self._http.post(self._ws_path("shipping/predictions/delivery"), request)

    # -- Savings ------------------------------------------------------------

    def get_savings(self) -> dict[str, Any]:
        """Get a summary of shipping cost savings for the workspace."""
        return self._http.get(self._ws_path("shipping/savings"))
