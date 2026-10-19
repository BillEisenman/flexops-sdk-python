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
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """List returns, optionally within a date range (ISO 8601 ``start_date`` and ``end_date``)."""
        query: dict[str, Any] = {}
        if page is not None:
            query["page"] = page
        if page_size is not None:
            query["pageSize"] = page_size
        if start_date is not None:
            query["startDate"] = start_date
        if end_date is not None:
            query["endDate"] = end_date
        return self._http.get(self._ws_path(), query or None)

    def get(self, return_id: str) -> dict[str, Any]:
        """Get a return authorization by ID."""
        return self._http.get(self._ws_path(return_id))

    def create(
        self,
        *,
        order_id: int,
        reason: str,
        items: list[dict[str, Any]],
        order_number: str | None = None,
        notes: str | None = None,
        customer_email: str | None = None,
        reason_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a return authorization (RMA).

        ``order_id`` is the numeric order ID. Each item is ``{"sku", "quantity", "reason"?}``.
        Returns the envelope (201) whose ``data`` is the new RMA.
        """
        fields = {
            "orderId": int(order_id),
            "orderNumber": order_number,
            "reason": reason,
            "items": items,
            "notes": notes,
            "customerEmail": customer_email,
            "reasonId": reason_id,
        }
        return self._http.post(self._ws_path("rma"), {k: v for k, v in fields.items() if v is not None})

    def generate_label(
        self,
        rma_number: str,
        *,
        weight_oz: float | None = None,
        length_in: float | None = None,
        width_in: float | None = None,
        height_in: float | None = None,
        carrier_code: str | None = None,
        service_type: str | None = None,
        payment_confirmed: bool | None = None,
        hazmat_classification: int | None = None,
        rate_indicator: str | None = None,
    ) -> dict[str, Any]:
        """Generate a return label for an approved RMA, identified by its RMA number.

        The carrier needs the package weight and all three dimensions: pass ``weight_oz``,
        ``length_in``, ``width_in`` and ``height_in``. Anything left out comes from the
        workspace's default shipping preset; with no preset the Gateway answers 400
        ``PackageMeasurementsRequired`` naming the missing fields.

        Only the arguments you set are sent. ``hazmat_classification`` (a ``HazmatClassification``)
        declares what the return holds. ``carrier_code`` defaults to ``usps`` on the Gateway.
        ``rate_indicator`` names a USPS flat-rate product (for example ``FS``) the customer returns
        in; it needs ``service_type`` ``PRIORITY`` or ``PRIORITY_EXPRESS``.
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
            "rateIndicator": rate_indicator,
        }
        # Always a JSON object: the Gateway binds a required GenerateReturnLabelRequest body
        # and refuses an empty one with 400.
        body = {key: value for key, value in fields.items() if value is not None}
        return self._http.post(self._ws_path(f"{rma_number}/label"), body)

    def mark_received(
        self,
        rma_id: int,
        *,
        rma_number: str,
        warehouse_id: int,
        inspected_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Receive and inspect a returned RMA, restocking or disposing of each item.

        Each inspected item is ``{"partNumber", "quantity", "disposition", "partDescription"?,
        "inspectionNotes"?}`` with ``disposition`` 0 (restock), 1 (dispose) or 2 (forward).
        """
        return self._http.post(self._ws_path(f"{rma_id}/receive"), {
            "rmaNumber": rma_number,
            "warehouseId": warehouse_id,
            "inspectedItems": inspected_items,
        })
