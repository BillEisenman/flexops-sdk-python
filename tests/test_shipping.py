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

WS_ID = "ws-test-001"


class TestShipping:
    @responses.activate
    def test_get_rates(self, client):
        rates = [
            {"carrier": "USPS", "service": "Priority Mail", "rate": 8.5, "currency": "USD", "estimatedDays": 2},
            {"carrier": "UPS", "service": "Ground", "rate": 12.3, "currency": "USD", "estimatedDays": 5},
        ]
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/rates",
            json={"success": True, "data": rates},
            status=200,
        )

        result = client.shipping.get_rates({"fromZip": "10001", "toZip": "90210", "weight": 16, "weightUnit": "oz"})

        assert len(result["data"]) == 2
        assert result["data"][0]["carrier"] == "USPS"

    @responses.activate
    def test_get_cheapest_rate(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/rates/cheapest",
            json={"success": True, "data": {"carrier": "USPS", "service": "Ground Advantage", "rate": 5.25, "currency": "USD", "estimatedDays": 4}},
            status=200,
        )

        result = client.shipping.get_cheapest_rate({"fromZip": "10001", "toZip": "90210", "weight": 8})

        assert result["data"]["rate"] == 5.25

    @responses.activate
    def test_validate_address(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/addresses/validate",
            json={"success": True, "data": {"isValid": True, "messages": []}},
            status=200,
        )

        result = client.shipping.validate_address({
            "name": "John Doe",
            "street1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "US",
        })

        assert result["data"]["isValid"] is True

    @responses.activate
    def test_track_shipment(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/track/9400111899223456789012",
            json={
                "success": True,
                "data": {
                    "trackingNumber": "9400111899223456789012",
                    "carrier": "USPS",
                    "status": "In Transit",
                    "events": [{"timestamp": "2026-03-04T10:00:00Z", "status": "Departed", "description": "Left facility"}],
                },
            },
            status=200,
        )

        result = client.shipping.track("9400111899223456789012")

        assert result["data"]["carrier"] == "USPS"
        assert len(result["data"]["events"]) == 1

    @responses.activate
    def test_create_label(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/labels",
            json={"success": True, "data": {"labelId": "lbl-001"}},
            status=200,
        )

        result = client.shipping.create_label({
            "carrier": "USPS",
            "service": "Priority Mail",
            "fromAddress": {"name": "A", "street1": "1 St", "city": "NY", "state": "NY", "zip": "10001", "country": "US"},
            "toAddress": {"name": "B", "street1": "2 St", "city": "LA", "state": "CA", "zip": "90210", "country": "US"},
            "parcel": {"weight": 16},
            "idempotencyKey": "idem-key-001",
        })

        assert result["data"]["labelId"] == "lbl-001"
