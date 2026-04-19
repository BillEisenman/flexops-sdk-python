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

    def generate_label(self, return_id: str) -> dict[str, Any]:
        """Generate a return label for an approved RMA."""
        return self._http.post(self._ws_path(f"{return_id}/label"))

    def mark_received(self, return_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Mark items as received."""
        return self._http.post(self._ws_path(f"{return_id}/receive"), {"items": items})

    def process_refund(self, return_id: str) -> dict[str, Any]:
        """Process refund for a return."""
        return self._http.post(self._ws_path(f"{return_id}/refund"))
