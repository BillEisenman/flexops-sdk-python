# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

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
    def test_fedex_rate_calculator(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/ApiProxy/api/v3/RateCalculator/postRetrieveFedExRateAndTransitTimesAsync",
            json={"success": True},
            status=200,
        )

        client.carriers.fedex.get_rates({"shipperPostalCode": "10001"})

        assert responses.calls[0].request.method == "POST"

    @responses.activate
    def test_dhl_create_shipment(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/ApiProxy/api/v2/ShippingLabel/postDhlCreateShipment",
            json={"success": True},
            status=200,
        )

        client.carriers.dhl.create_shipment({"productCode": "P"})

        assert "postDhlCreateShipment" in responses.calls[0].request.url

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
