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


class TestCarriers:
    @responses.activate
    def test_usps_address_validation(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/ApiProxy/api/v3/AddressValidation/getUspsValidateAndCorrectAddress",
            json={"success": True},
            status=200,
        )

        client.carriers.usps.validate_address({"zipCode": "10001"})

        assert len(responses.calls) == 1
        assert "getUspsValidateAndCorrectAddress" in responses.calls[0].request.url

    @responses.activate
    def test_dhl_read_goes_through_the_proxy_as_get(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/ApiProxy/api/v2/ShippingLabel/getDhlTrackSingleShipment",
            json={"success": True},
            status=200,
        )

        client.carriers.dhl.track({"trackingNumber": "1234567890"})

        assert responses.calls[0].request.method == "GET"

    def test_closed_label_routes_and_dhl_update_pickup_are_gone(self, client):
        # The Gateway answers 410 Gone for the proxy's label-generation routes; the proxy has no PATCH.
        for carrier, name in (("usps", "create_domestic_label"), ("usps", "create_return_label"),
                              ("usps", "create_international_label"), ("ups", "create_label"),
                              ("fedex", "create_shipment"), ("fedex", "create_return_shipment"),
                              ("dhl", "create_shipment"), ("dhl", "update_pickup")):
            assert not hasattr(getattr(client.carriers, carrier), name), f"{carrier}.{name}"

    @responses.activate
    def test_proxy_write_is_deprecated_and_keyed(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/ApiProxy/api/v3/RateCalculator/postRetrieveFedExRateAndTransitTimesAsync",
            json={"success": True},
        )

        with pytest.warns(DeprecationWarning, match="sunset 2027-06-30"):
            client.carriers.fedex.get_rates({"shipperPostalCode": "10001"})

        request = responses.calls[0].request
        assert request.method == "POST"
        assert json.loads(request.body) == {"shipperPostalCode": "10001"}
        assert request.headers["Idempotency-Key"]
        assert "deprecated" in client.carriers.fedex.get_rates.__doc__

    @responses.activate
    def test_proxy_delete_is_deprecated(self, client):
        responses.add(responses.DELETE, f"{BASE_URL}/api/ApiProxy/api/v2/ShippingLabel/deleteDhlPickup", status=204)

        with pytest.warns(DeprecationWarning):
            assert client.carriers.dhl.cancel_pickup() is None

    def test_reads_are_not_deprecated(self, client):
        assert not hasattr(client.carriers.usps.city_state_lookup, "__deprecated__")

    @responses.activate
    def test_ups_tracking(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/ApiProxy/api/v2/ShippingLabel/getSingleUpsTrackingDetail",
            json={"success": True},
            status=200,
        )

        client.carriers.ups.track({"trackingNumber": "1Z999AA10123456784"})

        assert "getSingleUpsTrackingDetail" in responses.calls[0].request.url
