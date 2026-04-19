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

    def test_has_all_15_resource_properties(self):
        client = FlexOps(base_url="http://localhost:5000")
        assert client.auth is not None
        assert client.workspaces is not None
        assert client.shipping is not None
        assert client.carriers is not None
        assert client.webhooks is not None
        assert client.wallet is not None
        assert client.insurance is not None
        assert client.returns is not None
        assert client.api_keys is not None
        assert client.analytics is not None
        assert client.orders is not None
        assert client.inventory is not None
        assert client.pickups is not None
        assert client.scan_forms is not None
        assert client.rules is not None

    def test_carrier_sub_resources(self):
        client = FlexOps(base_url="http://localhost:5000")
        assert client.carriers.usps is not None
        assert client.carriers.ups is not None
        assert client.carriers.fedex is not None
        assert client.carriers.dhl is not None
