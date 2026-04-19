# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any

from .._http import HttpClient


class AuthResource:
    """Authentication operations (login, register, password management)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate with email and password. Returns JWT tokens."""
        result = self._http.post("/api/Account/login", {"email": email, "password": password})
        if isinstance(result, dict) and result.get("data", {}).get("accessToken"):
            self._http.set_access_token(result["data"]["accessToken"])
        return result

    def register(
        self, *, email: str, password: str, first_name: str, last_name: str, company_name: str | None = None,
    ) -> dict[str, Any]:
        """Register a new account."""
        body: dict[str, Any] = {
            "email": email,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
        }
        if company_name:
            body["companyName"] = company_name
        return self._http.post("/api/Account/register", body)

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expired access token."""
        result = self._http.request(
            "POST",
            "/api/Account/refresh-token",
            headers={"X-Current-Session-Token": refresh_token},
        )
        if isinstance(result, dict) and result.get("data", {}).get("accessToken"):
            self._http.set_access_token(result["data"]["accessToken"])
        return result

    def logout(self) -> dict[str, Any]:
        """Log out and invalidate the current session."""
        return self._http.post("/api/Account/logout")

    def get_profile(self) -> dict[str, Any]:
        """Get the current user's profile."""
        return self._http.get("/api/Account/profile")

    def update_profile(self, data: dict[str, Any]) -> dict[str, Any]:
        """Update the current user's profile."""
        return self._http.put("/api/Account/profile", data)

    def change_password(self, current_password: str, new_password: str) -> dict[str, Any]:
        """Change the current user's password."""
        return self._http.post("/api/Account/change-password", {
            "currentPassword": current_password,
            "newPassword": new_password,
        })

    def forgot_password(self, email: str) -> dict[str, Any]:
        """Request a password reset email."""
        return self._http.post("/api/Account/forgot-password", {"email": email})

    def reset_password(self, token: str, new_password: str) -> dict[str, Any]:
        """Reset password using a reset token."""
        return self._http.post("/api/Account/reset-password", {"token": token, "newPassword": new_password})

    def verify_email(self, token: str) -> dict[str, Any]:
        """Verify email with the verification token."""
        return self._http.post("/api/Account/verify-email", {"token": token})
