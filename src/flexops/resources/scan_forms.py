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
from .._types import ScanFormRequest


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
        tracking_numbers: list[str] | ScanFormRequest,
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

        Instead of the tracking numbers and keyword arguments, you can pass a ``ScanFormRequest`` with the
        same fields, but not both. A request without ``request_id`` gets a generated one, as above; the
        model you pass is not changed.

        Returns the Gateway envelope; its ``data`` is the created form, also when the same
        ``request_id`` and inputs are sent again. Read it with ``ScanForm.model_validate(result["data"])``.
        Raises ``FlexOpsError`` with status 409 when the ``request_id`` was used with different inputs,
        when the packages already belong to a manifest, or when this or an earlier operation needs review
        (its message names the operation; do not resubmit those packages), and 400 when the request or
        package selection is refused. A 409 is not retried.
        """
        options = (manifest_date, request_id, origin_postal_code, warehouse_id)
        if isinstance(tracking_numbers, ScanFormRequest):
            if any(option is not None for option in options):
                raise TypeError("Pass the SCAN form fields in the ScanFormRequest or as keyword arguments, not both.")
            request = tracking_numbers
        else:
            request = ScanFormRequest(tracking_numbers=tracking_numbers, manifest_date=manifest_date,
                                      request_id=request_id, origin_postal_code=origin_postal_code,
                                      warehouse_id=warehouse_id)
        body: dict[str, Any] = request.model_dump(mode="json", by_alias=True, exclude_none=True)
        if not body.get("requestId"):
            body["requestId"] = str(uuid.uuid4())
        return self._http.post(self._ws_path(), body)

    def list(self) -> dict[str, Any]:
        """List the workspace's saved scan forms, newest mailing date first, including any whose
        outcome is unknown. ``data`` is a list of forms: read each with ``ScanForm.model_validate``."""
        return self._http.get(self._ws_path())

    def get(self, scan_form_id: str) -> dict[str, Any]:
        """Get a saved scan form by its ``scanFormId``. ``data`` is the form: read it with
        ``ScanForm.model_validate``. A form that does not exist raises ``FlexOpsError`` with status 404."""
        return self._http.get(self._ws_path(scan_form_id))
