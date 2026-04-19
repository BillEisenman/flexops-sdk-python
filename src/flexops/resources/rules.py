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


class RulesResource:
    """Shipping automation rules management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str = "") -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required.")
        base = f"/api/workspaces/{ws_id}/shipping-rules"
        return f"{base}/{suffix}" if suffix else base

    def list(self) -> dict[str, Any]:
        """List all shipping automation rules. Max 100 per workspace."""
        return self._http.get(self._ws_path())

    def get(self, rule_id: str) -> dict[str, Any]:
        """Get a rule by ID."""
        return self._http.get(self._ws_path(rule_id))

    def create(self, rule: dict[str, Any]) -> dict[str, Any]:
        """Create a shipping rule."""
        return self._http.post(self._ws_path(), rule)

    def update(self, rule_id: str, rule: dict[str, Any]) -> dict[str, Any]:
        """Update a shipping rule."""
        return self._http.put(self._ws_path(rule_id), rule)

    def delete(self, rule_id: str) -> dict[str, Any]:
        """Delete a shipping rule."""
        return self._http.delete(self._ws_path(rule_id))

    def reorder(self, rule_ids: list[str]) -> dict[str, Any]:
        """Reorder rules (set priority)."""
        return self._http.put(self._ws_path("reorder"), {"ruleIds": rule_ids})
