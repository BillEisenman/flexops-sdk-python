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
    """The workspace wallet, read-only.

    Funding, transactions and auto-reload are managed in the FlexOps portals, not through the API.
    """

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def get_balance(self) -> dict[str, Any]:
        """Get the configured workspace's wallet balance.

        Returns the bare ``{"hasWallet", "balanceCents", "balance"}`` object, not an envelope.
        """
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        return self._http.get("/api/wallet/my-balance", headers={"X-Workspace-Id": ws_id})
