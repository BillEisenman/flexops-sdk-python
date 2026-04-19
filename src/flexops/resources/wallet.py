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


class WalletResource:
    """Wallet balance and transaction management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        return f"/api/workspaces/{ws_id}/wallet/{suffix}"

    def get_balance(self) -> dict[str, Any]:
        """Get the current wallet balance."""
        return self._http.get(self._ws_path("balance"))

    def add_funds(self, amount: float) -> dict[str, Any]:
        """Add funds to the wallet."""
        return self._http.post(self._ws_path("add-funds"), {"amount": amount})

    def list_transactions(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """List wallet transactions."""
        query: dict[str, Any] = {}
        if page is not None:
            query["page"] = page
        if page_size is not None:
            query["pageSize"] = page_size
        if start_date is not None:
            query["startDate"] = start_date
        if end_date is not None:
            query["endDate"] = end_date
        return self._http.get(self._ws_path("transactions"), query or None)

    def configure_auto_reload(
        self,
        *,
        enabled: bool,
        threshold: float | None = None,
        amount: float | None = None,
    ) -> dict[str, Any]:
        """Configure auto-reload settings."""
        body: dict[str, Any] = {"enabled": enabled}
        if threshold is not None:
            body["threshold"] = threshold
        if amount is not None:
            body["amount"] = amount
        return self._http.put(self._ws_path("auto-reload"), body)
