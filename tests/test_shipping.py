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
            {"carrierCode": "USPS", "serviceCode": "PRIORITY", "rate": 8.5, "currency": "USD", "estimatedDays": 2},
            {"carrierCode": "UPS", "serviceCode": "GROUND", "rate": 12.3, "currency": "USD", "estimatedDays": 5},
        ]
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/shipping/rates",
            json={"currency": "USD", "rates": rates},
            status=200,
        )

        request = {
            "origin": {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001"},
            "destination": {"addressLine1": "456 Oak Ave", "city": "Los Angeles",
                            "stateProvince": "CA", "postalCode": "90210"},
            "package": {"weight": 16, "weightUnit": "oz"},
        }
        result = client.shipping.get_rates(request)

        assert len(result["rates"]) == 2
        assert result["rates"][0]["carrierCode"] == "USPS"
        assert json.loads(responses.calls[0].request.body) == request

    @responses.activate
    def test_get_cheapest_rate(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/shipping/rates/cheapest",
            json={"carrierCode": "USPS", "serviceCode": "GROUND_ADVANTAGE",
                  "rate": 5.25, "currency": "USD", "estimatedDays": 4},
            status=200,
        )

        result = client.shipping.get_cheapest_rate({
            "origin": {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001"},
            "destination": {"addressLine1": "456 Oak Ave", "city": "Los Angeles",
                            "stateProvince": "CA", "postalCode": "90210"},
            "package": {"weight": 8, "weightUnit": "oz"},
        })

        assert result["rate"] == 5.25

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
                    "events": [{"timestamp": "2026-03-04T10:00:00Z", "status": "Departed",
                                "description": "Left facility"}],
                },
            },
            status=200,
        )

        result = client.shipping.track("9400111899223456789012")

        assert result["data"]["carrier"] == "USPS"
        assert len(result["data"]["events"]) == 1

    @responses.activate
    def test_create_label(self, client):
        from flexops import CreateLabelRequest, LabelPurchasePreview

        request = CreateLabelRequest(
            carrier_code="USPS", service_code="GROUND_ADVANTAGE",
            origin={"addressLine1": "1 St", "city": "NY", "stateProvince": "NY", "postalCode": "10001"},
            destination={"addressLine1": "2 St", "city": "LA", "stateProvince": "CA", "postalCode": "90210"},
            package={"weight": 16}, maximum_postage_amount=10.25,
        )
        url = f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/labels"
        preview = dict(status="Preview", quotedPostageAmount=8.5, maximumPostageAmount=10.25,
                       currency="USD", expiresAt="2026-09-19T00:05:00Z", confirmationToken="approval")
        responses.add(responses.POST, url, json=preview)
        result = client.shipping.create_label(request)
        assert LabelPurchasePreview.model_validate(result).confirmation_token == "approval"
        assert len(responses.calls) == 1  # Never automatically confirm.
        body = json.loads(responses.calls[0].request.body)
        assert body["maximumPostageAmount"] == 10.25
        assert body["origin"]["addressLine1"] == "1 St"
        assert "confirmationToken" not in body
        assert "carrier" not in body
        request.confirmation_token = result["confirmationToken"]
        responses.add(responses.POST, url, json={"message": "temporary"}, status=503)
        responses.add(responses.POST, url, json={"labelId": "lbl-001", "carrierCode": "USPS"}, status=201)
        result = client.shipping.create_label(request, idempotency_key="purchase-001")
        assert result["labelId"] == "lbl-001"
        for call in responses.calls[1:]:
            assert call.request.headers["Idempotency-Key"] == "purchase-001"
            assert json.loads(call.request.body)["confirmationToken"] == "approval"
        assert responses.calls[1].request.body == responses.calls[2].request.body
        responses.add(responses.POST, url, json=preview)
        assert client.shipping.create_label(body)["status"] == "Preview"
        assert "Idempotency-Key" not in responses.calls[3].request.headers

    @responses.activate
    def test_label_approval_errors(self, client):
        import pytest

        from flexops import FlexOpsError
        url = f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/labels"
        for status, code in [(400, "ApprovalRequired"), (409, "ApprovalExpired")]:
            responses.add(responses.POST, url, json={"errorCode": code, "message": code}, status=status)
            with pytest.raises(FlexOpsError) as error:
                client.shipping.create_label({"maximumPostageAmount": 0})
            assert error.value.status == status
            assert error.value.code == code
        assert len(responses.calls) == 2

    @responses.activate
    def test_international_customs_typed_contract(self, client):
        from pathlib import Path

        from flexops import CreateLabelRequest
        fixture = json.loads((Path(__file__).parents[1] / "examples/international-label.json").read_text())
        request = CreateLabelRequest.model_validate(fixture)
        url = f"{BASE_URL}/api/workspaces/{WS_ID}/shipping/labels"
        responses.add(responses.POST, url, json={"status": "Preview", "confirmationToken": "approved"}, status=200)
        result = client.shipping.create_label(request)
        assert result["status"] == "Preview"
        assert len(responses.calls) == 1
        sent = json.loads(responses.calls[0].request.body)
        assert sent["customsDeclaration"] == fixture["customsDeclaration"]
        assert sent["orderId"] == 42
        assert sent["shipDate"] == "2099-01-01"
        request.confirmation_token = result["confirmationToken"]
        responses.add(responses.POST, url, json={"labelId": "intl-1", "currency": "USD"}, status=201)
        client.shipping.create_label(request, idempotency_key="international-1")
        assert responses.calls[1].request.headers["Idempotency-Key"] == "international-1"
        assert json.loads(responses.calls[1].request.body)["customsDeclaration"] == fixture["customsDeclaration"]

    @responses.activate
    def test_international_disabled_no_retry(self, client):
        import pytest

        from flexops import FlexOpsError
        responses.add(responses.POST, f"{BASE_URL}/api/shipping/rates",
                      json={"errorCode": "FeatureDisabled", "message": "International disabled"}, status=403)
        with pytest.raises(FlexOpsError) as error:
            client.shipping.get_rates({})
        assert error.value.code == "FeatureDisabled"
        assert len(responses.calls) == 1
