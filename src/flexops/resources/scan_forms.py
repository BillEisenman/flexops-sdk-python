# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Callable

from .._http import HttpClient


class ScanFormsResource:
    """USPS scan form (SCAN/manifest) management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/scan-forms"
        return f"{base}/{suffix}" if suffix else base

    def create(
        self,
        tracking_numbers: list[str],
        *,
        manifest_date: date | str | None = None,
        request_id: str | None = None,
        origin_postal_code: str | None = None,
        warehouse_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a USPS scan form (SCAN/manifest) for 1 to 1,000 tracking numbers.

        API keys need ``shipping:write``; the public demo keys are refused.

        ``manifest_date`` is the labels' mailing date (a ``date`` or ``YYYY-MM-DD``). Live creation
        needs it: without it the Gateway answers 400 ``Choose the label mailing date.`` The sandbox
        defaults it to today (UTC), which is why it is optional here.

        ``request_id`` identifies the operation. Repeating a request with the same ID returns the same
        form instead of creating another; reusing it with different inputs is 409. When omitted, one is
        generated for this call and sent on every retry of it, so a retry cannot create a second form.
        Pass your own to retry the call yourself after an unknown outcome.

        ``origin_postal_code`` is the origin ZIP group to manifest; ``warehouse_id`` limits package
        selection to one warehouse.
        """
        body: dict[str, Any] = {
            "trackingNumbers": tracking_numbers,
            "requestId": request_id or str(uuid.uuid4()),
        }
        if manifest_date is not None:
            body["manifestDate"] = manifest_date.isoformat() if isinstance(manifest_date, date) else manifest_date
        if origin_postal_code is not None:
            body["originPostalCode"] = origin_postal_code
        if warehouse_id is not None:
            body["warehouseId"] = warehouse_id
        return self._http.post(self._ws_path(), body)

    def list(self) -> dict[str, Any]:
        """List scan forms."""
        return self._http.get(self._ws_path())

    def get(self, scan_form_id: str) -> dict[str, Any]:
        """Get a scan form by ID."""
        return self._http.get(self._ws_path(scan_form_id))
