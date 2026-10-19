# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

import json

import pytest
import responses

from tests.conftest import BASE_URL


class TestAuth:
    @responses.activate
    def test_login_uses_the_returned_token(self, client_no_key):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/Account/login",
            json={
                "success": True,
                "data": {
                    "token": "jwt-token-123",
                    "refreshToken": "refresh-456",
                    "expiresAt": "2026-03-05T00:00:00Z",
                    "userId": "user-001",
                    "requiresTwoFactor": False,
                },
            },
            status=200,
        )
        responses.add(responses.GET, f"{BASE_URL}/api/workspaces", json={"success": True, "data": []})

        result = client_no_key.auth.login("test@flexops.io", "password123")
        client_no_key.workspaces.list()

        assert result["data"]["token"] == "jwt-token-123"
        assert json.loads(responses.calls[0].request.body) == {"email": "test@flexops.io", "password": "password123"}
        assert responses.calls[1].request.headers["Authorization"] == "Bearer jwt-token-123"

    @responses.activate
    def test_refresh_token_sends_both_tokens_in_the_body(self, client_no_key):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/Account/refresh-token",
            json={"success": True, "data": {"token": "new-jwt", "refreshToken": "new-refresh"}},
            status=200,
        )
        client_no_key.set_access_token("old-jwt")

        result = client_no_key.auth.refresh_token("old-refresh")
        client_no_key.auth.refresh_token("new-refresh", access_token="explicit-jwt")

        assert result["data"]["token"] == "new-jwt"
        assert json.loads(responses.calls[0].request.body) == {"token": "old-jwt", "refreshToken": "old-refresh"}
        assert json.loads(responses.calls[1].request.body) == {"token": "explicit-jwt", "refreshToken": "new-refresh"}
        assert "X-Current-Session-Token" not in responses.calls[0].request.headers
        assert client_no_key._http.access_token == "new-jwt"

    def test_refresh_token_needs_an_access_token(self, client_no_key):
        with pytest.raises(ValueError, match="access token"):
            client_no_key.auth.refresh_token("refresh-456")
