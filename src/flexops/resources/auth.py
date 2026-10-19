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
    """Token acquisition for user-token operations (login, refresh, logout).

    Account management (registration, profile, passwords) is done in the FlexOps portals.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate with email and password and use the returned access token.

        Returns the envelope whose ``data`` is the Gateway ``LoginResponse``: ``token`` (the access
        token), ``refreshToken``, ``expiresAt``, ``userId``, ``requiresTwoFactor`` and so on.
        """
        result = self._http.post("/api/Account/login", {"email": email, "password": password})
        self._use_token(result)
        return result

    def refresh_token(self, refresh_token: str, access_token: str | None = None) -> dict[str, Any]:
        """Exchange a refresh token, with the access token it was issued with, for new tokens.

        ``access_token`` defaults to the client's current access token. The new access token
        (``data["token"]``) replaces it.

        Raises:
            ValueError: No access token was passed and the client has none.
        """
        token = access_token or self._http.access_token
        if not token:
            raise ValueError("refresh_token needs the current access token; pass access_token or log in first.")
        result = self._http.post("/api/Account/refresh-token", {"token": token, "refreshToken": refresh_token})
        self._use_token(result)
        return result

    def _use_token(self, result: Any) -> None:
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict) and data.get("token"):
            self._http.set_access_token(data["token"])

    def logout(self) -> dict[str, Any]:
        """Log out and invalidate the current session."""
        return self._http.post("/api/Account/logout")
