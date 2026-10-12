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


class ReturnsResource:
    """Return authorization (RMA) management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/returns"
        return f"{base}/{suffix}" if suffix else base

    def list(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List all return authorizations."""
        query: dict[str, Any] = {}
        if page is not None:
            query["page"] = page
        if page_size is not None:
            query["pageSize"] = page_size
        if status is not None:
            query["status"] = status
        return self._http.get(self._ws_path(), query or None)

    def get(self, return_id: str) -> dict[str, Any]:
        """Get a return authorization by ID."""
        return self._http.get(self._ws_path(return_id))

    def create(self, *, order_id: str, reason: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a return authorization (RMA)."""
        return self._http.post(self._ws_path(), {
            "orderId": order_id,
            "reason": reason,
            "items": items,
        })

    def approve(self, return_id: str) -> dict[str, Any]:
        """Approve a return authorization."""
        return self._http.post(self._ws_path(f"{return_id}/approve"))

    def reject(self, return_id: str, reason: str) -> dict[str, Any]:
        """Reject a return authorization."""
        return self._http.post(self._ws_path(f"{return_id}/reject"), {"reason": reason})

    def cancel(self, return_id: str) -> dict[str, Any]:
        """Cancel a return authorization."""
        return self._http.post(self._ws_path(f"{return_id}/cancel"))

    def generate_label(
        self,
        return_id: str,
        *,
        weight_oz: float | None = None,
        length_in: float | None = None,
        width_in: float | None = None,
        height_in: float | None = None,
        carrier_code: str | None = None,
        service_type: str | None = None,
        payment_confirmed: bool | None = None,
        hazmat_classification: int | None = None,
    ) -> dict[str, Any]:
        """Generate a return label for an approved RMA.

        The carrier needs the package weight and all three dimensions: pass ``weight_oz``,
        ``length_in``, ``width_in`` and ``height_in``. Anything left out comes from the
        workspace's default shipping preset; with no preset the Gateway answers 400
        ``PackageMeasurementsRequired`` naming the missing fields.

        Only the arguments you set are sent. ``hazmat_classification`` (a ``HazmatClassification``)
        declares what the return holds.
        """
        fields = {
            "carrierCode": carrier_code,
            "serviceType": service_type,
            "weightOz": weight_oz,
            "lengthIn": length_in,
            "widthIn": width_in,
            "heightIn": height_in,
            "paymentConfirmed": payment_confirmed,
            "hazmatClassification": None if hazmat_classification is None else int(hazmat_classification),
        }
        # Always a JSON object: the Gateway binds a required GenerateReturnLabelRequest body
        # and refuses an empty one with 400.
        body = {key: value for key, value in fields.items() if value is not None}
        return self._http.post(self._ws_path(f"{return_id}/label"), body)

    def mark_received(self, return_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Mark items as received."""
        return self._http.post(self._ws_path(f"{return_id}/receive"), {"items": items})

    def process_refund(self, return_id: str) -> dict[str, Any]:
        """Process refund for a return."""
        return self._http.post(self._ws_path(f"{return_id}/refund"))
