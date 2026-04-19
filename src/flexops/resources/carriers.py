# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Any

from .._http import HttpClient


def _proxy(path: str) -> str:
    return f"/api/ApiProxy/{path.lstrip('/')}"


class _UspsCarrier:
    """USPS carrier operations via VisionSuite API proxy (V3 endpoints)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def validate_address(self, params: dict[str, str]) -> Any:
        """Validate and correct a US address via USPS."""
        return self._http.get(_proxy("api/v3/AddressValidation/getUspsValidateAndCorrectAddress"), params)

    def city_state_lookup(self, zip_code: str) -> Any:
        """City/State lookup by ZIP code."""
        return self._http.get(_proxy("api/v3/AddressValidation/getUspsCityStateLookupByZipCode"), {"zipCode": zip_code})

    def zip_code_lookup(self, params: dict[str, str]) -> Any:
        """ZIP code lookup by address."""
        return self._http.get(_proxy("api/v3/AddressValidation/getUspsZipCodeLookupByAddress"), params)

    def get_domestic_rates(self, body: Any) -> Any:
        """Search domestic shipping rates."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchDomesticBaseRates"), body)

    def get_domestic_products(self, body: Any) -> Any:
        """Search domestic product eligibility."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchEligibleDomesticProducts"), body)

    def get_domestic_prices(self, body: Any) -> Any:
        """Search domestic prices."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchEligibleDomesticPrices"), body)

    def get_international_rates(self, body: Any) -> Any:
        """Search international rates."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchInternationalBaseRates"), body)

    def get_international_prices(self, body: Any) -> Any:
        """Search international prices."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchEligibleInternationalPrices"), body)

    def create_domestic_label(self, body: Any) -> Any:
        """Generate a domestic shipping label."""
        return self._http.post(_proxy("api/v3/Shipping/postUspsGenerateDomesticShippingLabel"), body)

    def create_return_label(self, body: Any) -> Any:
        """Generate a domestic return label."""
        return self._http.post(_proxy("api/v3/Shipping/postUspsGenerateDomesticReturnsShippingLabel"), body)

    def create_international_label(self, body: Any) -> Any:
        """Generate an international shipping label."""
        return self._http.post(_proxy("api/v3/Shipping/postUspsGenerateInternationalShippingLabel"), body)

    def cancel_domestic_label(self) -> Any:
        """Cancel a domestic label."""
        return self._http.delete(_proxy("api/v3/Shipping/cancelUspsDomesticShipmentLabel"))

    def cancel_international_label(self) -> Any:
        """Cancel an international label."""
        return self._http.delete(_proxy("api/v3/Shipping/cancelUspsInternationalShipmentLabel"))

    def track_summary(self, params: dict[str, str]) -> Any:
        """Get tracking summary."""
        return self._http.get(_proxy("api/v3/Tracking/getUspsTrackingSummaryInformation"), params)

    def track_detail(self, params: dict[str, str]) -> Any:
        """Get detailed tracking info."""
        return self._http.get(_proxy("api/v3/Tracking/getUspsTrackingDetailInformation"), params)

    def create_pickup(self, body: Any) -> Any:
        """Schedule a carrier pickup."""
        return self._http.post(_proxy("api/v3/CarrierPickup/postUspsCreateCarrierPickupSchedule"), body)

    def cancel_pickup(self) -> Any:
        """Cancel a pickup."""
        return self._http.delete(_proxy("api/v3/CarrierPickup/cancelUspsCarrierPickupSchedule"))

    def create_scan_form(self, body: Any) -> Any:
        """Create a scan form."""
        return self._http.post(_proxy("api/v3/ScanForm/postUspsCreateScanFormLabelShipment"), body)

    def delivery_standards(self, params: dict[str, str]) -> Any:
        """Get delivery standards estimates."""
        return self._http.get(_proxy("api/v3/ServiceStandards/getUspsGetDeliveryStandardsEstimates"), params)

    def find_drop_off_locations(self, params: dict[str, str]) -> Any:
        """Find drop-off locations."""
        return self._http.get(_proxy("api/v3/LocationSearch/getUspsFindValidDropOffLocations"), params)

    def find_post_offices(self, params: dict[str, str]) -> Any:
        """Find post office locations."""
        return self._http.get(_proxy("api/v3/LocationSearch/getUspsFindValidPostOfficeLocations"), params)


class _UpsCarrier:
    """UPS carrier operations via VisionSuite API proxy (V2 endpoints)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def validate_address(self, body: Any) -> Any:
        """Verify an address via UPS."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsVerifyAddress"), body)

    def get_rates(self, body: Any) -> Any:
        """Get UPS rate quotes."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsRateCheck"), body)

    def create_label(self, body: Any) -> Any:
        """Generate a UPS shipping label."""
        return self._http.post(_proxy("api/v2/ShippingLabel/generateNewUpsShipLabel"), body)

    def track(self, params: dict[str, str]) -> Any:
        """Track a UPS shipment."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getSingleUpsTrackingDetail"), params)

    def create_pickup(self, body: Any) -> Any:
        """Create a UPS pickup."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsCreatePickup"), body)

    def cancel_pickup(self) -> Any:
        """Cancel a UPS pickup."""
        return self._http.delete(_proxy("api/v2/ShippingLabel/deleteUpsPickup"))

    def get_transit_times(self, body: Any) -> Any:
        """Get UPS transit times."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsGetTransitTimes"), body)

    def get_landed_cost(self, body: Any) -> Any:
        """Get UPS landed cost quote (international)."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsGetLandedCostQuote"), body)

    def search_locations(self, body: Any) -> Any:
        """Search UPS locations."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsSearchLocations"), body)

    def upload_document(self, body: Any) -> Any:
        """Upload paperless trade document."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsUploadPaperlessDocument"), body)

    def create_freight_shipment(self, body: Any) -> Any:
        """Create UPS freight shipment."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsCreateFreightShipment"), body)

    def get_freight_rate(self, body: Any) -> Any:
        """Get UPS freight rate."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsGetFreightRate"), body)


class _FedExCarrier:
    """FedEx carrier operations via VisionSuite API proxy (V3 endpoints)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def validate_address(self, body: Any) -> Any:
        """Validate a domestic address via FedEx."""
        return self._http.post(_proxy("api/v3/AddressValidation/postFedExValidateAndCorrectDomesticAddress"), body)

    def validate_postal_code(self, body: Any) -> Any:
        """Validate a postal code."""
        return self._http.post(_proxy("api/v3/AddressValidation/postFedExValidatePostalCode"), body)

    def get_rates(self, body: Any) -> Any:
        """Get FedEx rate and transit times."""
        return self._http.post(_proxy("api/v3/RateCalculator/postRetrieveFedExRateAndTransitTimesAsync"), body)

    def create_shipment(self, body: Any) -> Any:
        """Create a FedEx shipment."""
        return self._http.post(_proxy("api/v3/Shipping/postFedExCreateNewShipment"), body)

    def cancel_shipment(self, body: Any) -> Any:
        """Cancel a FedEx shipment."""
        return self._http.put(_proxy("api/v3/Shipping/putFedExCancelShipment"), body)

    def validate_shipment(self, body: Any) -> Any:
        """Validate a shipment (dry run)."""
        return self._http.post(_proxy("api/v3/Shipping/postFedExValidateShipment"), body)

    def create_return_shipment(self, body: Any) -> Any:
        """Create a return shipment."""
        return self._http.post(_proxy("api/v3/Shipping/postFedExCreateNewReturnShipment"), body)

    def track(self, body: Any) -> Any:
        """Track by tracking number."""
        return self._http.post(_proxy("api/v3/Tracking/postFedExRetrieveTrackingInfoByTrackingNumber"), body)

    def track_multi_piece(self, body: Any) -> Any:
        """Track multi-piece shipment."""
        return self._http.post(_proxy("api/v3/Tracking/postFedExRetrieveTrackingInfoForMultiPieceShipment"), body)

    def register_tracking_notification(self, body: Any) -> Any:
        """Register for tracking notifications."""
        return self._http.post(_proxy("api/v3/Tracking/postFedExRegisterForTrackingNotification"), body)

    def create_pickup(self, body: Any) -> Any:
        """Create a carrier pickup."""
        return self._http.post(_proxy("api/v3/CarrierPickup/postFedExCreateCarrierPickupRequest"), body)

    def cancel_pickup(self, body: Any) -> Any:
        """Cancel a pickup."""
        return self._http.put(_proxy("api/v3/CarrierPickup/putFedExCancelCarrierPickupRequest"), body)

    def search_locations(self, body: Any) -> Any:
        """Search valid locations."""
        return self._http.post(_proxy("api/v3/LocationSearch/postFedExSearchValidLocations"), body)

    def get_service_standards(self, body: Any) -> Any:
        """Get service standards and transit times."""
        return self._http.post(_proxy("api/v3/ServiceStandards/postFedExRetrieveServicesAndTransitTimes"), body)

    def get_freight_rate(self, body: Any) -> Any:
        """Get freight rate quote."""
        return self._http.post(_proxy("api/v3/Freight/postFedExGetFreightRateQuote"), body)

    def create_freight_shipment(self, body: Any) -> Any:
        """Create freight shipment."""
        return self._http.post(_proxy("api/v3/Freight/postFedExCreateFreightShipment"), body)

    def ground_close(self, body: Any) -> Any:
        """Ground close with documents."""
        return self._http.post(_proxy("api/v3/GroundClose/postFedExCloseWithDocuments"), body)

    def upload_trade_documents(self, body: Any) -> Any:
        """Upload trade documents."""
        return self._http.post(_proxy("api/v3/Trade/postFedExUploadTradeDocuments"), body)

    def create_open_shipment(self, body: Any) -> Any:
        """Create an open shipment."""
        return self._http.post(_proxy("api/v3/OpenShip/postFedExCreateOpenShipment"), body)

    def add_packages_to_open_shipment(self, body: Any) -> Any:
        """Add packages to an open shipment."""
        return self._http.post(_proxy("api/v3/OpenShip/postFedExAddPackagesToOpenShipment"), body)

    def confirm_open_shipment(self, body: Any) -> Any:
        """Confirm and finalize an open shipment."""
        return self._http.post(_proxy("api/v3/OpenShip/postFedExConfirmOpenShipment"), body)


class _DhlCarrier:
    """DHL carrier operations via VisionSuite API proxy (V2 endpoints)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def validate_address(self, params: dict[str, str]) -> Any:
        """Validate an address via DHL."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlValidateAddress"), params)

    def get_rates(self, params: dict[str, str]) -> Any:
        """Get DHL shipping rates."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlRates"), params)

    def get_multi_piece_rates(self, body: Any) -> Any:
        """Get multi-piece rates."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlMultiPieceRates"), body)

    def get_products(self, params: dict[str, str]) -> Any:
        """Get DHL products/services."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlProducts"), params)

    def create_shipment(self, body: Any) -> Any:
        """Create a DHL shipment (label)."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlCreateShipment"), body)

    def track(self, params: dict[str, str]) -> Any:
        """Track a DHL shipment."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlTrackSingleShipment"), params)

    def track_multiple(self, params: dict[str, str]) -> Any:
        """Track multiple DHL shipments."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlTrackMultipleShipments"), params)

    def create_pickup(self, body: Any) -> Any:
        """Create a DHL pickup."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlCreatePickup"), body)

    def update_pickup(self, body: Any) -> Any:
        """Update a DHL pickup."""
        return self._http.patch(_proxy("api/v2/ShippingLabel/patchDhlUpdatePickup"), body)

    def cancel_pickup(self) -> Any:
        """Cancel a DHL pickup."""
        return self._http.delete(_proxy("api/v2/ShippingLabel/deleteDhlPickup"))

    def calculate_landed_cost(self, body: Any) -> Any:
        """Calculate landed cost (duties/taxes)."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlCalculateLandedCost"), body)

    def screen_shipment(self, body: Any) -> Any:
        """Screen a shipment for compliance."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlScreenShipment"), body)

    def upload_invoice(self, body: Any) -> Any:
        """Upload an invoice."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlUploadInvoice"), body)

    def get_proof_of_delivery(self, params: dict[str, str]) -> Any:
        """Get electronic proof of delivery."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlElectronicProofOfDelivery"), params)

    def get_reference_data(self, params: dict[str, str]) -> Any:
        """Get reference data (countries, services, etc.)."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlReferenceData"), params)

    def find_service_points(self, params: dict[str, str]) -> Any:
        """Find DHL service points."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlServicePoints"), params)


class CarriersResource:
    """Direct carrier operations via the VisionSuite Core Services API proxy.

    Use ``client.shipping`` for normalized operations, or these carrier-specific
    methods when you need full control over the carrier payload.

    Example::

        # USPS domestic label
        label = client.carriers.usps.create_domestic_label({...})

        # FedEx rate quote
        rates = client.carriers.fedex.get_rates({...})
    """

    def __init__(self, http: HttpClient) -> None:
        self.usps = _UspsCarrier(http)
        self.ups = _UpsCarrier(http)
        self.fedex = _FedExCarrier(http)
        self.dhl = _DhlCarrier(http)
