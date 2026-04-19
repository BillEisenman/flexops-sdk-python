# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

import json

import responses

from tests.conftest import BASE_URL


class TestAuth:
    @responses.activate
    def test_login_and_stores_token(self, client_no_key):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/Account/login",
            json={
                "success": True,
                "data": {
                    "accessToken": "jwt-token-123",
                    "refreshToken": "refresh-456",
                    "expiresAt": "2026-03-05T00:00:00Z",
                    "userId": "user-001",
                },
            },
            status=200,
        )

        result = client_no_key.auth.login("test@flexops.io", "password123")

        assert result["success"] is True
        assert result["data"]["accessToken"] == "jwt-token-123"
        req = responses.calls[0].request
        body = json.loads(req.body)
        assert body["email"] == "test@flexops.io"
        assert body["password"] == "password123"

    @responses.activate
    def test_refresh_token(self, client_no_key):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/Account/refresh-token",
            json={
                "success": True,
                "data": {
                    "accessToken": "new-jwt",
                    "refreshToken": "new-refresh",
                    "expiresAt": "2026-03-06T00:00:00Z",
                    "userId": "user-001",
                },
            },
            status=200,
        )

        result = client_no_key.auth.refresh_token("old-refresh-token")

        assert result["data"]["accessToken"] == "new-jwt"
        req = responses.calls[0].request
        assert req.headers["X-Current-Session-Token"] == "old-refresh-token"
