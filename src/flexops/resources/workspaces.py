# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any, Callable, Literal

from .._http import HttpClient


class WorkspacesResource:
    """Workspace CRUD and membership management."""

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str | None = None) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required. Set it via client.workspace_id or config.")
        return f"/api/workspaces/{ws_id}/{suffix}" if suffix else f"/api/workspaces/{ws_id}"

    def list(self) -> dict[str, Any]:
        """List all workspaces the current user belongs to."""
        return self._http.get("/api/workspaces")

    def get(self, workspace_id: str | None = None) -> dict[str, Any]:
        """Get details for a specific workspace."""
        ws_id = workspace_id or self._get_workspace_id()
        return self._http.get(f"/api/workspaces/{ws_id}")

    def create(self, name: str, plan_id: str | None = None) -> dict[str, Any]:
        """Create a new workspace."""
        body: dict[str, Any] = {"name": name}
        if plan_id:
            body["planId"] = plan_id
        return self._http.post("/api/workspaces", body)

    def update(self, data: dict[str, Any]) -> dict[str, Any]:
        """Update workspace settings."""
        return self._http.put(self._ws_path(), data)

    def list_members(self) -> dict[str, Any]:
        """List members of the current workspace."""
        return self._http.get(self._ws_path("members"))

    def invite_member(
        self, email: str, role: Literal["Owner", "Admin", "Member", "Guest"] = "Member",
    ) -> dict[str, Any]:
        """Invite a user to the workspace."""
        return self._http.post(self._ws_path("members/invite"), {"email": email, "role": role})

    def remove_member(self, user_id: str) -> dict[str, Any]:
        """Remove a member from the workspace."""
        return self._http.delete(self._ws_path(f"members/{user_id}"))

    def update_member_role(self, user_id: str, role: Literal["Owner", "Admin", "Member", "Guest"]) -> dict[str, Any]:
        """Update a member's role."""
        return self._http.put(self._ws_path(f"members/{user_id}/role"), {"role": role})
