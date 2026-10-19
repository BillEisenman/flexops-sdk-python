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


class EmailTemplatesResource:
    """Shipment notification email templates, one per tracking event.

    Reads work with any API key or a user token. Writes need a user token (``auth.login``) or an API
    key granted the ``email-templates:write`` scope; a key without it gets 403 ``API_KEY_SCOPE_REQUIRED``
    naming ``requiredScopes``. ``preview`` counts as a write.

    Responses are bare JSON. ``eventType`` is a ``TrackingEmailEvent`` number; ``upsert`` creates or
    replaces the template for that event.
    """

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/email-templates"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> list[dict[str, Any]]:
        """List the workspace's email templates."""
        return self._http.get(self._ws_path())

    def get(self, template_id: str) -> dict[str, Any]:
        """Get an email template."""
        return self._http.get(self._ws_path(template_id))

    def upsert(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create or replace the template for ``request["eventType"]``.

        ``request`` is the Gateway ``UpsertEmailTemplateRequest``: ``eventType``, ``subjectTemplate``
        (up to 500 characters) and ``htmlBodyTemplate`` are required; ``isEnabled`` defaults to true.
        """
        return self._http.put(self._ws_path(), request)

    def delete(self, template_id: str) -> None:
        """Delete an email template (204)."""
        return self._http.delete(self._ws_path(template_id))

    def preview(self, *, subject_template: str, html_body_template: str) -> dict[str, Any]:
        """Render a subject and body with sample data. Returns ``{"renderedSubject", "renderedHtmlBody"}``."""
        body = {"subjectTemplate": subject_template, "htmlBodyTemplate": html_body_template}
        return self._http.post(self._ws_path("preview"), body)
