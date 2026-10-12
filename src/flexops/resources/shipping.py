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
from .._types import Address, CreateLabelRequest, RateRequest, ShippingAddress


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

    def get_rates(self, request: dict[str, Any] | RateRequest) -> dict[str, Any]:
        """Get shipping rates from all configured carriers."""
        return self._http.post("/api/shipping/rates", _to_body(request))

    def get_cheapest_rate(self, request: dict[str, Any] | RateRequest) -> dict[str, Any]:
        """Get the single cheapest rate across all carriers."""
        return self._http.post("/api/shipping/rates/cheapest", _to_body(request))

    def get_fastest_rate(self, request: dict[str, Any] | RateRequest) -> dict[str, Any]:
        """Get the single fastest rate across all carriers."""
        return self._http.post("/api/shipping/rates/fastest", _to_body(request))

    # -- Labels -------------------------------------------------------------

    def create_label(self, request: dict[str, Any] | CreateLabelRequest,
                     *, idempotency_key: str | None = None) -> dict[str, Any]:
        """Preview postage, or purchase with explicit confirmation and an idempotency key.

        Returns the raw preview (status=Preview) or purchased label, never an envelope.
        Reuse the purchase key when retrying an uncertain outcome. A label without an
        ``order_id`` must declare ``hazmat_classification``; the SDK never fills it in.
        """
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key is not None else None
        return self._http.post("/api/shipping/labels", _to_body(request), headers=headers)

    def cancel_label(self, label_id: str) -> dict[str, Any]:
        """Cancel (void) a shipping label."""
        return self._http.delete(self._ws_path(f"shipping/labels/{label_id}"))

    # -- Tracking -----------------------------------------------------------

    def track(self, tracking_number: str) -> dict[str, Any]:
        """Track a shipment by tracking number."""
        return self._http.get(self._ws_path(f"shipping/track/{tracking_number}"))

    # -- Address Validation -------------------------------------------------

    def validate_address(self, address: dict[str, Any] | ShippingAddress | Address) -> dict[str, Any]:
        """Validate and correct a shipping address.

        Sends the Gateway ``AddressValidationRequest`` (``{"address": {...}}``). A legacy
        ``street1``/``state``/``zip`` address is mapped to the Gateway field names.
        """
        return self._http.post("/api/shipping/addresses/validate", {"address": _to_shipping_address(address)})

    # -- Batch Labels -------------------------------------------------------

    def create_batch(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create labels in batch.

        The payload is sent as given. Include ``hazmatClassification`` only when you have a
        declaration; the SDK never adds one.
        """
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


_LEGACY_ADDRESS_FIELDS = {
    "street1": "addressLine1",
    "street2": "addressLine2",
    "state": "stateProvince",
    "zip": "postalCode",
    "country": "countryCode",
}


def _to_body(request: Any) -> Any:
    """Serializes a typed request with Gateway field names; unset fields are left out."""
    if isinstance(request, (CreateLabelRequest, RateRequest)):
        return request.model_dump(by_alias=True, exclude_none=True)
    return request


def _to_shipping_address(address: dict[str, Any] | ShippingAddress | Address) -> dict[str, Any]:
    """Maps an address to the Gateway ``ShippingAddress``; canonical input passes through."""
    if isinstance(address, (ShippingAddress, Address)):
        address = address.model_dump(by_alias=True, exclude_none=True)
    if "street1" not in address:
        return address
    return {_LEGACY_ADDRESS_FIELDS.get(key, key): value for key, value in address.items() if value is not None}
