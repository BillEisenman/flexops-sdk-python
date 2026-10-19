# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-10-19
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Callable

from .._http import HttpClient


class ReportSchedulesResource:
    """Scheduled reports emailed to recipients.

    Reads work with any API key or a user token. Writes need a user token (``auth.login``) or an API
    key granted the ``report-schedules:write`` scope; a key without it gets 403 ``API_KEY_SCOPE_REQUIRED``
    naming ``requiredScopes``.

    Responses use the ``{"success", "data", "message"}`` envelope, except ``delete`` (204).
    ``format`` is a ``ReportFormat`` and ``frequencyType`` a ``ReportFrequency`` number.
    """

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/report-schedules"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> dict[str, Any]:
        """List the workspace's report schedules (envelope of a list)."""
        return self._http.get(self._ws_path())

    def get(self, id: str) -> dict[str, Any]:
        """Get a report schedule (envelope)."""
        return self._http.get(self._ws_path(id))

    def create(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create a report schedule (201, envelope).

        ``request`` is the Gateway ``CreateReportScheduleRequest``: ``reportType`` (free text, such as
        ``"shipments"``), ``format``, ``frequencyType``, ``timeOfDayUtc`` (``"HH:mm:ss"``) and
        ``recipientEmails`` (comma-separated) are required; ``filterParametersJson``, ``dayOfWeek``
        (0-6, Sunday 0, for weekly), ``dayOfMonth`` (1-28, for monthly) and ``maxFailures`` are optional.
        """
        return self._http.post(self._ws_path(), request)

    def update(self, id: str, request: dict[str, Any]) -> dict[str, Any]:
        """Update a report schedule (envelope). Every ``create`` field is optional here."""
        return self._http.put(self._ws_path(id), request)

    def delete(self, id: str) -> None:
        """Delete a report schedule (204)."""
        return self._http.delete(self._ws_path(id))

    def toggle(self, id: str) -> dict[str, Any]:
        """Flip a report schedule's ``isEnabled`` (envelope with ``data`` null)."""
        return self._http.post(self._ws_path(f"{id}/toggle"))
