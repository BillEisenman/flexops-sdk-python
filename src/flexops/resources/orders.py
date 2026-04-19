# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any

from .._http import HttpClient


class OrdersResource:
    """Order management via VisionSuite API proxy."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    @staticmethod
    def _path(endpoint: str) -> str:
        return f"/api/ApiProxy/api/v1/Order/{endpoint}"

    def create(self, order: Any) -> dict[str, Any]:
        """Create a new order."""
        return self._http.post(self._path("postNewOrder"), order)

    def get_new_orders(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get new orders awaiting processing."""
        return self._http.get(self._path("getNewOrderList"), params)

    def get_by_status(self, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Get all orders filtered by status."""
        return self._http.get(self._path("getAllOrderListByStatus"), params)

    def get_details(self, order_number: str) -> dict[str, Any]:
        """Get complete order details by order number."""
        return self._http.get(self._path("getCompleteOrderDetailsByOrderNumber"), {"orderNumber": order_number})

    def get_extended_details(self, order_number: str) -> dict[str, Any]:
        """Get extended order details by order number."""
        return self._http.get(self._path("getExtendedOrderDetailsByOrderNumber"), {"orderNumber": order_number})

    def get_status(self, order_number: str) -> dict[str, Any]:
        """Get order status by order number."""
        return self._http.get(self._path("getIndividualOrderStatusByOrderNumber"), {"orderNumber": order_number})

    def cancel(self, order_number: str) -> dict[str, Any]:
        """Cancel an order."""
        return self._http.post(self._path("cancelOrderByOrderNumber"), {"orderNumber": order_number})

    def get_items(self, order_number: str) -> dict[str, Any]:
        """Get all items for an order."""
        return self._http.get(self._path("getAllOrderItemsByOrderNumber"), {"orderNumber": order_number})

    def get_ship_methods(self) -> dict[str, Any]:
        """Get available ship methods."""
        return self._http.get(self._path("getAvailableShipMethodsList"))

    def get_warehouses(self) -> dict[str, Any]:
        """Get active warehouse list."""
        return self._http.get(self._path("getActiveWarehouseList"))

    def get_country_codes(self) -> dict[str, Any]:
        """Get country codes."""
        return self._http.get(self._path("getCountryNameCodeList"))

    def get_status_types(self) -> dict[str, Any]:
        """Get order status types."""
        return self._http.get(self._path("getOrderStatusTypesList"))
