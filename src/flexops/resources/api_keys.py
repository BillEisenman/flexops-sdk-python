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


class ApiKeysResource:
    """API key management (create, revoke, rotate)."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/api-keys"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> dict[str, Any]:
        """List all API keys for the workspace."""
        return self._http.get(self._ws_path())

    def create(
        self, name: str, *, scopes: list[str] | None = None, expires_in_days: int | None = None,
    ) -> dict[str, Any]:
        """Create a new API key. The full key is only returned once."""
        body: dict[str, Any] = {"name": name}
        if scopes is not None:
            body["scopes"] = scopes
        if expires_in_days is not None:
            body["expiresInDays"] = expires_in_days
        return self._http.post(self._ws_path(), body)

    def revoke(self, key_id: str) -> dict[str, Any]:
        """Revoke an API key."""
        return self._http.delete(self._ws_path(key_id))

    def rotate(self, key_id: str) -> dict[str, Any]:
        """Rotate an API key (revoke + create new)."""
        return self._http.post(self._ws_path(f"{key_id}/rotate"))
