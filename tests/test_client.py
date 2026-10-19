# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from flexops import FlexOps


class TestClientInitialization:
    def test_creates_client_with_defaults(self):
        client = FlexOps(base_url="http://localhost:5000")
        assert client is not None
        assert client.workspace_id is None

    def test_creates_client_with_api_key_and_workspace(self):
        client = FlexOps(
            base_url="http://localhost:5000",
            api_key="fxk_test_abc123",
            workspace_id="ws-test-001",
        )
        assert client.workspace_id == "ws-test-001"

    def test_allows_changing_workspace_id(self):
        client = FlexOps(base_url="http://localhost:5000", workspace_id="ws-test-001")
        client.workspace_id = "ws-new-001"
        assert client.workspace_id == "ws-new-001"

    def test_exposes_the_documented_resources(self):
        client = FlexOps(base_url="http://localhost:5000")
        for name in ("auth", "workspaces", "shipping", "carriers", "webhooks", "wallet", "insurance", "returns",
                     "analytics", "orders", "inventory", "pickups", "scan_forms", "rules", "carbon_offsets",
                     "recurring_shipments", "report_schedules", "email_templates",
                     "hs_codes"):
            assert getattr(client, name) is not None, name

    def test_portal_only_resources_are_gone(self):
        client = FlexOps(base_url="http://localhost:5000")
        # reports was renamed report_schedules.
        for name in ("api_keys", "reports", "offsets"):
            assert not hasattr(client, name), name

    def test_carrier_sub_resources(self):
        client = FlexOps(base_url="http://localhost:5000")
        assert client.carriers.usps is not None
        assert client.carriers.ups is not None
        assert client.carriers.dhl is not None
        assert client.carriers.fedex is not None
