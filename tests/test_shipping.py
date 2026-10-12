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
        from flexops import ShippingAddress

        responses.add(
            responses.POST,
            f"{BASE_URL}/api/shipping/addresses/validate",
            json={"isValid": True, "messages": []},
            status=200,
        )
        canonical = {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY",
                     "postalCode": "10001", "countryCode": "US"}

        result = client.shipping.validate_address({
            "name": "John Doe",
            "street1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "US",
        })
        client.shipping.validate_address(canonical)
        client.shipping.validate_address(ShippingAddress.model_validate(canonical))

        assert result["isValid"] is True
        assert json.loads(responses.calls[0].request.body) == {"address": {"name": "John Doe", **canonical}}
        assert json.loads(responses.calls[1].request.body) == {"address": canonical}
        assert json.loads(responses.calls[2].request.body) == {"address": canonical}

    @responses.activate
    def test_track_shipment(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/shipping/track/9400111899223456789012",
            json={
                "trackingNumber": "9400111899223456789012",
                "carrierCode": "USPS",
                "status": "In Transit",
                "events": [{"timestamp": "2026-03-04T10:00:00Z", "description": "Left facility"}],
            },
            status=200,
        )

        result = client.shipping.track("9400111899223456789012")

        assert result["carrierCode"] == "USPS"
        assert len(result["events"]) == 1

    @responses.activate
    def test_create_label(self, client):
        from flexops import CreateLabelRequest, LabelPurchasePreview

        request = CreateLabelRequest(
            carrier_code="USPS", service_code="GROUND_ADVANTAGE",
            origin={"addressLine1": "1 St", "city": "NY", "stateProvince": "NY", "postalCode": "10001"},
            destination={"addressLine1": "2 St", "city": "LA", "stateProvince": "CA", "postalCode": "90210"},
            package={"weight": 16}, maximum_postage_amount=10.25,
        )
        url = f"{BASE_URL}/api/shipping/labels"
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
        url = f"{BASE_URL}/api/shipping/labels"
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
        url = f"{BASE_URL}/api/shipping/labels"
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


class TestHazmatClassification:
    """The HAZMAT declaration is sent only when the caller sets it; the SDK never defaults it."""

    request = {
        "carrier_code": "USPS", "service_code": "PRIORITY",
        "origin": {"addressLine1": "1 St", "city": "NY", "stateProvince": "NY", "postalCode": "10001"},
        "destination": {"addressLine1": "2 St", "city": "LA", "stateProvince": "CA", "postalCode": "90210"},
        "package": {"weight": 16},
    }

    def test_values_match_the_gateway_enum(self):
        from flexops import HazmatClassification

        assert {c.name: int(c) for c in HazmatClassification} == {
            "NONE": 0, "LIMITED_QUANTITY": 1, "LITHIUM_BATTERY_CONTAINED_IN_EQUIPMENT": 2,
            "LITHIUM_BATTERY_PACKED_WITH_EQUIPMENT": 3, "LITHIUM_BATTERY_STANDALONE": 4,
            "OTHER_RESTRICTED": 5, "LITHIUM_BATTERY_USED_DEVICE": 6,
        }

    @responses.activate
    def test_label_sends_hazmat_only_when_set(self, client):
        from flexops import CreateLabelRequest, HazmatClassification

        responses.add(responses.POST, f"{BASE_URL}/api/shipping/labels", json={"labelId": "l", "isSandbox": True})
        client.shipping.create_label(CreateLabelRequest(**self.request))
        none = HazmatClassification.NONE
        client.shipping.create_label(CreateLabelRequest(**self.request, hazmat_classification=none))
        client.shipping.create_label(CreateLabelRequest(**self.request, hazmat_classification=1))
        client.shipping.create_label({"carrierCode": "USPS", "hazmatClassification": 0})

        sent = [json.loads(call.request.body) for call in responses.calls]
        assert "hazmatClassification" not in sent[0]
        assert sent[1]["hazmatClassification"] == 0
        assert sent[2]["hazmatClassification"] == 1
        assert sent[3]["hazmatClassification"] == 0

    @responses.activate
    def test_rate_request_sends_hazmat_only_when_set(self, client):
        from flexops import HazmatClassification, RateRequest

        for path in ("rates", "rates/cheapest", "rates/fastest"):
            responses.add(responses.POST, f"{BASE_URL}/api/shipping/{path}", json={"rates": []})
        fields = {k: v for k, v in self.request.items() if k in ("origin", "destination", "package")}
        client.shipping.get_rates(RateRequest(**fields))
        client.shipping.get_rates(RateRequest(**fields, hazmat_classification=HazmatClassification.NONE))
        client.shipping.get_cheapest_rate(RateRequest(**fields, hazmat_classification=4))
        client.shipping.get_fastest_rate(RateRequest(**fields))

        sent = [json.loads(call.request.body) for call in responses.calls]
        assert "hazmatClassification" not in sent[0]
        assert sent[1]["hazmatClassification"] == 0
        assert sent[2]["hazmatClassification"] == 4
        assert "hazmatClassification" not in sent[3]
        assert sent[0]["origin"]["addressLine1"] == "1 St"

    @responses.activate
    def test_return_label_sends_hazmat_only_when_set(self, client):
        from flexops import HazmatClassification

        responses.add(responses.POST, f"{BASE_URL}/api/workspaces/{WS_ID}/returns/RMA-1/label", json={"success": True})
        client.returns.generate_label("RMA-1")
        client.returns.generate_label("RMA-1", hazmat_classification=HazmatClassification.NONE)

        # The Gateway binds a required GenerateReturnLabelRequest body; {} takes its defaults.
        assert json.loads(responses.calls[0].request.body) == {}
        assert json.loads(responses.calls[1].request.body) == {"hazmatClassification": 0}


class TestShippingGatewayRoutes:
    """The api/Shipping routes are not workspace-scoped (Gateway ShippingController)."""

    @responses.activate
    def test_cancel_label_sends_carrier_code(self, client):
        import pytest

        responses.add(responses.DELETE, f"{BASE_URL}/api/shipping/labels/lbl-1", json={"success": True},
                      match=[responses.matchers.query_param_matcher({"carrierCode": "USPS"})])
        assert client.shipping.cancel_label("lbl-1", "USPS")["success"] is True
        assert client.shipping.cancel_label("lbl-1", carrier_code="USPS")["success"] is True
        with pytest.raises(ValueError, match="carrier_code"):
            client.shipping.cancel_label("lbl-1")
        assert len(responses.calls) == 2

    @responses.activate
    def test_read_and_ai_calls_use_gateway_routes(self, client):
        responses.add(responses.GET, f"{BASE_URL}/api/shipping/carriers", json=[{"carrierCode": "USPS"}])
        responses.add(responses.POST, f"{BASE_URL}/api/shipping/recommendations", json={"lane": "100->902"})
        responses.add(responses.POST, f"{BASE_URL}/api/shipping/predictions/delivery", json={"carrierCode": "USPS"})
        responses.add(responses.GET, f"{BASE_URL}/api/shipping/savings", json={"lanesAnalyzed": 3})

        assert client.shipping.get_carriers()[0]["carrierCode"] == "USPS"
        assert client.shipping.get_recommendations({"originPostalCode": "10001"})["lane"] == "100->902"
        assert client.shipping.predict_delivery({"carrierCode": "USPS"})["carrierCode"] == "USPS"
        assert client.shipping.get_savings()["lanesAnalyzed"] == 3
        assert json.loads(responses.calls[1].request.body) == {"originPostalCode": "10001"}


class TestBatchLabels:
    """CreateBatchLabelRequest mirrors the Gateway batch body (orders plus package measurements)."""

    @responses.activate
    def test_typed_batch_matches_gateway_shape(self, client):
        from flexops import BatchLabelItem, CreateBatchLabelRequest, HazmatClassification

        for path in ("labels/batch", "labels/batch/preview"):
            responses.add(responses.POST, f"{BASE_URL}/api/workspaces/{WS_ID}/{path}", json={"success": True})
        request = CreateBatchLabelRequest(items=[
            BatchLabelItem(order_id=42, package_weight_in_ounces=16, package_length_in_inches=10,
                           package_width_in_inches=6, package_height_in_inches=4, carrier_code="USPS",
                           hazmat_classification=HazmatClassification.NONE),
            BatchLabelItem(order_id=43, package_weight_in_ounces=8, package_length_in_inches=6,
                           package_width_in_inches=4, package_height_in_inches=2),
        ], callback_url="https://example.test/hook")

        client.shipping.create_batch(request)
        client.shipping.preview_batch(request)

        sent = json.loads(responses.calls[0].request.body)
        assert sent == {
            "items": [
                {"orderId": 42, "packageWeightInOunces": 16, "packageLengthInInches": 10,
                 "packageWidthInInches": 6, "packageHeightInInches": 4, "carrierCode": "USPS",
                 "deliveryConfirmationRequired": False, "signatureConfirmationRequired": False,
                 "insuranceCoverageRequested": False, "labelFormat": "PDF", "hazmatClassification": 0},
                {"orderId": 43, "packageWeightInOunces": 8, "packageLengthInInches": 6,
                 "packageWidthInInches": 4, "packageHeightInInches": 2,
                 "deliveryConfirmationRequired": False, "signatureConfirmationRequired": False,
                 "insuranceCoverageRequested": False, "labelFormat": "PDF"},
            ],
            "callbackUrl": "https://example.test/hook",
            "dryRun": False,
        }
        assert json.loads(responses.calls[1].request.body) == sent

    @responses.activate
    def test_dict_batch_is_sent_as_given(self, client):
        responses.add(responses.POST, f"{BASE_URL}/api/workspaces/{WS_ID}/labels/batch", json={"success": True})
        client.shipping.create_batch({"items": [{"orderId": 1}]})
        assert json.loads(responses.calls[0].request.body) == {"items": [{"orderId": 1}]}
