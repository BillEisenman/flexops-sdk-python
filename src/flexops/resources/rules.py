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
        """Create a shipping rule.

        ``rule`` is ``{"name", "priority", "isEnabled", "warehouseId"?, "conditions", "actions"}``; each
        condition is ``{"field", "operator", "value", "group"?}`` and each action ``{"type", "value"}``.

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        return self._http.post(self._ws_path(), rule)

    def update(self, rule_id: str, rule: dict[str, Any]) -> dict[str, Any]:
        """Update a shipping rule. ``rule`` takes the fields of ``create``; the ones left out are kept.

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        return self._http.put(self._ws_path(rule_id), rule)

    def delete(self, rule_id: str) -> None:
        """Delete a shipping rule. The Gateway answers 204 No Content, so this returns ``None``.

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        return self._http.delete(self._ws_path(rule_id))

    def reorder(self, rules: list[str] | list[dict[str, Any]]) -> dict[str, Any]:
        """Set rule priorities.

        Pass ``[{"ruleId", "priority"}, ...]``, or rule IDs in evaluation order, which are given
        priorities 0, 1, 2 and so on (lower is evaluated first).

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        items = [
            rule if isinstance(rule, dict) else {"ruleId": rule, "priority": index}
            for index, rule in enumerate(rules)
        ]
        return self._http.post(self._ws_path("reorder"), {"rules": items})

    def test(self, request: dict[str, Any]) -> dict[str, Any]:
        """Dry-run the workspace's rules against a sample shipment and trace which one wins.

        ``request`` is the Gateway ``TestShippingRuleRequest``: ``destinationCountry`` plus optional
        ``weightOz``, ``declaredValue``, ``destinationState``, ``destinationPostalCode``,
        ``orderSource``, ``itemCount``, ``shipMethod``, ``destinationZone`` and ``tags``.

        Changes nothing. API keys need ``shipping:read``; the public demo keys are refused.
        """
        return self._http.post(self._ws_path("test"), request)
