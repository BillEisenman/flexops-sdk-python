# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

import pytest
import responses

from flexops import FlexOps, FlexOpsAuthError, FlexOpsError, FlexOpsRateLimitError
from tests.conftest import BASE_URL


class TestErrorHandling:
    @responses.activate
    def test_throws_auth_error_on_401(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/workspaces",
            json={"message": "Invalid token"},
            status=401,
        )

        with pytest.raises(FlexOpsAuthError):
            client.workspaces.list()

    @responses.activate
    def test_throws_flexops_error_on_400(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/workspaces/ws-test-001/shipping/rates",
            json={"message": "Validation failed", "errors": ["weight is required"]},
            status=400,
        )

        with pytest.raises(FlexOpsError) as exc_info:
            client.shipping.get_rates({"fromZip": "", "toZip": "", "weight": 0})
        assert exc_info.value.status == 400
        assert exc_info.value.errors == ["weight is required"]

    @responses.activate
    def test_throws_rate_limit_error_on_429(self):
        for _ in range(3):
            responses.add(
                responses.GET,
                f"{BASE_URL}/api/workspaces",
                json={"message": "Rate limited"},
                status=429,
                headers={"retry-after": "60"},
            )

        client = FlexOps(
            base_url=BASE_URL,
            api_key="fxk_test_abc123",
            workspace_id="ws-test-001",
            retry={"max_retries": 1, "base_delay": 0.01},
        )

        with pytest.raises(FlexOpsRateLimitError):
            client.workspaces.list()

    @responses.activate
    def test_retries_on_500_errors(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/workspaces",
            json={"message": "Internal error"},
            status=500,
        )
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/workspaces",
            json={"success": True, "data": []},
            status=200,
        )

        client = FlexOps(
            base_url=BASE_URL,
            api_key="fxk_test_abc123",
            workspace_id="ws-test-001",
            retry={"max_retries": 2, "base_delay": 0.01},
        )

        result = client.workspaces.list()
        assert result["success"] is True
        assert len(responses.calls) == 2

    @responses.activate
    def test_forbidden_error_on_403(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/workspaces",
            json={"message": "Access denied"},
            status=403,
        )

        with pytest.raises(FlexOpsError) as exc_info:
            client.workspaces.list()
        assert exc_info.value.status == 403
        assert exc_info.value.code == "FORBIDDEN"
