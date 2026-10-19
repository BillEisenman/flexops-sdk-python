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
from .._types import Address, CreateBatchLabelRequest, CreateLabelRequest, RateRequest, ShippingAddress


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

    def cancel_label(self, label_id: str, carrier_code: str | None = None) -> dict[str, Any]:
        """Cancel (void) a shipping label.

        ``carrier_code`` (for example ``"USPS"``) is required by the Gateway; it is optional here
        only so older call sites fail with a clear error instead of a TypeError.
        """
        if not carrier_code:
            raise ValueError("carrier_code is required to cancel a label (for example 'USPS').")
        return self._http.delete(
            f"/api/shipping/labels/{quote(label_id, safe='')}?carrierCode={quote(carrier_code, safe='')}")

    # -- Tracking -----------------------------------------------------------

    def track(self, tracking_number: str) -> dict[str, Any]:
        """Track a shipment by tracking number."""
        return self._http.get(f"/api/shipping/track/{quote(tracking_number, safe='')}")

    # -- Address Validation -------------------------------------------------

    def validate_address(self, address: dict[str, Any] | ShippingAddress | Address) -> dict[str, Any]:
        """Validate a shipping address against the carriers' validation services.

        Sends the Gateway ``AddressValidationRequest``, a flat ``{"name"?, "line1", "line2"?, "city",
        "state"?, "postalCode", "country"}``. A ``ShippingAddress`` (``addressLine1``,
        ``stateProvince``, ``countryCode``) or legacy ``street1``/``state``/``zip`` address is mapped
        to those names. Returns the bare ``AddressValidationResult`` (``isValid``,
        ``suggestedAddress``, ``isResidential``, ``warnings``, ``validatedBy``,
        ``validationUnavailable``, ``checkedAt``); ``validationUnavailable`` means no carrier could
        check the address, not that it was rejected.
        """
        ws_id = self._get_workspace_id()
        headers = {"X-Workspace-Id": ws_id} if ws_id else None
        return self._http.post("/api/addresses/validate", _to_validation_address(address), headers=headers)

    # -- Batch Labels -------------------------------------------------------

    def create_batch(self, request: dict[str, Any] | CreateBatchLabelRequest) -> dict[str, Any]:
        """Create labels in batch.

        A dict is sent as given. Set ``hazmatClassification`` on an item only when you have
        a declaration; the SDK never adds one.
        """
        return self._http.post(self._ws_path("labels/batch"), _to_body(request))

    def preview_batch(self, request: dict[str, Any] | CreateBatchLabelRequest) -> dict[str, Any]:
        """Preview a batch without purchasing (dry-run)."""
        return self._http.post(self._ws_path("labels/batch/preview"), _to_body(request))

    def get_batch_status(self, job_id: str) -> dict[str, Any]:
        """Get batch job status."""
        return self._http.get(self._ws_path(f"labels/batch/{job_id}"))

    def download_batch_label(self, job_id: str, item_id: str) -> bytes:
        """Download a label from a batch job."""
        return self._http.get(self._ws_path(f"labels/batch/{job_id}/items/{item_id}/label"))

    # -- Carriers -----------------------------------------------------------

    def get_carriers(self) -> dict[str, Any]:
        """List available carriers and their services."""
        return self._http.get("/api/shipping/carriers")

    # -- Recommendations & Predictions --------------------------------------

    def get_recommendations(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get AI-powered shipping service recommendations."""
        return self._http.post("/api/shipping/recommendations", request)

    def predict_delivery(self, request: dict[str, Any]) -> dict[str, Any]:
        """Predict the delivery date for a prospective shipment."""
        return self._http.post("/api/shipping/predictions/delivery", request)

    # -- Savings ------------------------------------------------------------

    def get_savings(self) -> dict[str, Any]:
        """Get a summary of shipping cost savings for the workspace."""
        return self._http.get("/api/shipping/savings")


# ShippingAddress and legacy Address names for each AddressValidationRequest field.
_VALIDATION_FIELDS = {
    "name": ("name",),
    "line1": ("line1", "addressLine1", "street1"),
    "line2": ("line2", "addressLine2", "street2"),
    "city": ("city",),
    "state": ("state", "stateProvince"),
    "postalCode": ("postalCode", "zip"),
    "country": ("country", "countryCode"),
}


def _to_body(request: Any) -> Any:
    """Serializes a typed request with Gateway field names; unset fields are left out."""
    if isinstance(request, (CreateLabelRequest, RateRequest, CreateBatchLabelRequest)):
        return request.model_dump(by_alias=True, exclude_none=True)
    return request


def _to_validation_address(address: dict[str, Any] | ShippingAddress | Address) -> dict[str, Any]:
    """Maps an address to the flat Gateway ``AddressValidationRequest``; other fields are left out."""
    if isinstance(address, (ShippingAddress, Address)):
        address = address.model_dump(by_alias=True, exclude_none=True)
    body: dict[str, Any] = {}
    for field, sources in _VALIDATION_FIELDS.items():
        value = next((address[key] for key in sources if address.get(key) is not None), None)
        if value is not None:
            body[field] = value
    return body
