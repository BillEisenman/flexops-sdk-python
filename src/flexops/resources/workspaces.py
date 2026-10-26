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
from .._types import WorkspaceRole

RoleName = Literal["Owner", "Admin", "Member", "Merchant"]


def _to_role(role: WorkspaceRole | RoleName | int) -> int:
    """Maps a role name or number to the Gateway ``WorkspaceRole`` number."""
    if isinstance(role, str):
        try:
            return int(WorkspaceRole[role.upper()])
        except KeyError:
            raise ValueError(f"Unknown workspace role: {role}. Use Owner, Admin, Member or Merchant.") from None
    return int(WorkspaceRole(role))


class WorkspacesResource:
    """Workspaces the caller belongs to and their membership.

    Workspaces are created and configured in the FlexOps portals.
    """

    def __init__(self, http: HttpClient, get_workspace_id: Callable[[], str | None]) -> None:
        self._http = http
        self._get_workspace_id = get_workspace_id

    def _ws_path(self, suffix: str | None = None) -> str:
        ws_id = self._get_workspace_id()
        if not ws_id:
            raise ValueError("workspace_id is required. Set it via client.workspace_id or config.")
        return f"/api/workspaces/{ws_id}/{suffix}" if suffix else f"/api/workspaces/{ws_id}"

    def list(self) -> dict[str, Any]:
        """List the workspaces the caller belongs to.

        Returns the envelope whose ``data`` is a list of workspace summaries (``id``, ``name``,
        ``slug``, ``myRole`` as a ``WorkspaceRole`` number, ``planId``, ``memberCount``, ...).
        """
        return self._http.get("/api/workspaces")

    def get(self, workspace_id: str | None = None) -> dict[str, Any]:
        """Get details for a workspace (the configured one by default)."""
        ws_id = workspace_id or self._get_workspace_id()
        return self._http.get(f"/api/workspaces/{ws_id}")

    def list_members(self) -> dict[str, Any]:
        """List members of the current workspace.

        Returns the envelope whose ``data`` is ``{"members": [...], "pendingInvites": [...],
        "userLimit", "activeCount", "canInviteMore"}``; each member's ``role`` is a number.
        """
        return self._http.get(self._ws_path("members"))

    def invite_member(self, email: str, role: WorkspaceRole | RoleName | int = WorkspaceRole.MEMBER) -> dict[str, Any]:
        """Invite a user to the workspace. Needs the Owner or Admin role.

        ``role`` is a ``WorkspaceRole``, its name (``"Admin"``) or its number; it is sent as the number.

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        return self._http.post(self._ws_path("members/invite"), {"email": email, "role": _to_role(role)})

    def remove_member(self, user_id: str) -> dict[str, Any]:
        """Remove a member from the workspace.

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        return self._http.delete(self._ws_path(f"members/{user_id}"))

    def update_member_role(self, user_id: str, role: WorkspaceRole | RoleName | int) -> dict[str, Any]:
        """Change a member's role. ``role`` is a ``WorkspaceRole``, its name or its number.

        Signed-in users only: API keys get 403 ``SIGNED_IN_USER_REQUIRED``, whatever their scopes.
        """
        return self._http.put(self._ws_path(f"members/{user_id}/role"), {"newRole": _to_role(role)})
