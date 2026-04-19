# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Literal

from .._http import HttpClient


class AnalyticsResource:
    """Analytics and reporting (shipments, orders, carriers, returns)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    @staticmethod
    def _path(endpoint: str) -> str:
        return f"/api/ApiProxy/api/v4/Analytics/{endpoint}"

    def _date_params(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if period:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return params or None

    def shipments_trend(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Shipments trend over time."""
        return self._http.get(self._path("ShipmentsTrend"), self._date_params(start_date, end_date, period))

    def carrier_summary(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Carrier usage summary."""
        return self._http.get(self._path("CarrierSummary"), self._date_params(start_date, end_date, period))

    def top_destinations(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Top shipping destinations."""
        return self._http.get(self._path("TopDestinations"), self._date_params(start_date, end_date, period, limit))

    def inventory_metrics(self) -> dict[str, Any]:
        """Inventory metrics (stock levels, low-stock alerts)."""
        return self._http.get(self._path("InventoryMetrics"))

    def stock_by_warehouse(self) -> dict[str, Any]:
        """Stock levels by warehouse."""
        return self._http.get(self._path("StockByWarehouse"))

    def order_metrics(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Order metrics (volume, revenue)."""
        return self._http.get(self._path("OrderMetrics"), self._date_params(start_date, end_date, period))

    def order_trend(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Order trend over time."""
        return self._http.get(self._path("OrderTrend"), self._date_params(start_date, end_date, period))

    def top_selling_products(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Top selling products."""
        return self._http.get(self._path("TopSellingProducts"), self._date_params(start_date, end_date, period, limit))

    def returns_metrics(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Returns metrics."""
        return self._http.get(self._path("ReturnsMetrics"), self._date_params(start_date, end_date, period))

    def returns_trend(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Returns trend over time."""
        return self._http.get(self._path("ReturnsTrend"), self._date_params(start_date, end_date, period))

    def return_reasons(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Return reasons breakdown."""
        return self._http.get(self._path("ReturnReasons"), self._date_params(start_date, end_date, period))

    def performance_metrics(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Fulfillment performance metrics."""
        return self._http.get(self._path("PerformanceMetrics"), self._date_params(start_date, end_date, period))

    def carrier_performance(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Carrier delivery performance."""
        return self._http.get(self._path("CarrierPerformance"), self._date_params(start_date, end_date, period))

    def shipping_cost_analytics(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Shipping cost analytics."""
        return self._http.get(self._path("ShippingCostAnalytics"), self._date_params(start_date, end_date, period))

    def delivery_performance(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> dict[str, Any]:
        """Delivery performance (on-time percentage)."""
        return self._http.get(self._path("DeliveryPerformance"), self._date_params(start_date, end_date, period))
