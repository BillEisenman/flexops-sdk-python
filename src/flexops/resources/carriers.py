# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

import functools
import warnings
from typing import Any, Callable, TypeVar

from .._http import HttpClient

_F = TypeVar("_F", bound=Callable[..., Any])

PROXY_DEPRECATION = (
    "Legacy carrier proxy (sunset 2027-06-30). Needs a user token: API keys get 403 API_KEY_SCOPE_REQUIRED. "
    "Use client.shipping / client.pickups / client.scan_forms where they cover this."
)


def _proxy(path: str) -> str:
    return f"/api/ApiProxy/{path.lstrip('/')}"


def _deprecated(method: _F) -> _F:
    """Marks a carrier proxy write deprecated: warns on each call and records ``__deprecated__``."""

    @functools.wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(f"{method.__qualname__}: {PROXY_DEPRECATION}", DeprecationWarning, stacklevel=2)
        return method(*args, **kwargs)

    wrapper.__doc__ = f"{method.__doc__}\n\n        .. deprecated:: 3.0.0\n            {PROXY_DEPRECATION}\n        "
    wrapper.__deprecated__ = PROXY_DEPRECATION  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


class _UspsCarrier:
    """USPS carrier operations via VisionSuite API proxy (V3 endpoints).

    With an API key, address, ZIP, city and location lookups require ``shipping:read``, tracking
    requires ``tracking:read`` and delivery standards require ``rates:read``. Writes are deprecated and
    need a user token.
    """

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

    @_deprecated
    def get_domestic_rates(self, body: Any) -> Any:
        """Search domestic shipping rates."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchDomesticBaseRates"), body)

    @_deprecated
    def get_domestic_products(self, body: Any) -> Any:
        """Search domestic product eligibility."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchEligibleDomesticProducts"), body)

    @_deprecated
    def get_domestic_prices(self, body: Any) -> Any:
        """Search domestic prices."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchEligibleDomesticPrices"), body)

    @_deprecated
    def get_international_rates(self, body: Any) -> Any:
        """Search international rates."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchInternationalBaseRates"), body)

    @_deprecated
    def get_international_prices(self, body: Any) -> Any:
        """Search international prices."""
        return self._http.post(_proxy("api/v3/RateCalculator/postUspsSearchEligibleInternationalPrices"), body)

    @_deprecated
    def cancel_domestic_label(self) -> Any:
        """Cancel a domestic label."""
        return self._http.delete(_proxy("api/v3/Shipping/cancelUspsDomesticShipmentLabel"))

    @_deprecated
    def cancel_international_label(self) -> Any:
        """Cancel an international label."""
        return self._http.delete(_proxy("api/v3/Shipping/cancelUspsInternationalShipmentLabel"))

    def track_summary(self, params: dict[str, str]) -> Any:
        """Get tracking summary."""
        return self._http.get(_proxy("api/v3/Tracking/getUspsTrackingSummaryInformation"), params)

    def track_detail(self, params: dict[str, str]) -> Any:
        """Get detailed tracking info."""
        return self._http.get(_proxy("api/v3/Tracking/getUspsTrackingDetailInformation"), params)

    @_deprecated
    def create_pickup(self, body: Any) -> Any:
        """Schedule a carrier pickup."""
        return self._http.post(_proxy("api/v3/CarrierPickup/postUspsCreateCarrierPickupSchedule"), body)

    @_deprecated
    def cancel_pickup(self) -> Any:
        """Cancel a pickup."""
        return self._http.delete(_proxy("api/v3/CarrierPickup/cancelUspsCarrierPickupSchedule"))

    @_deprecated
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
    """UPS carrier operations via VisionSuite API proxy (V2 endpoints).

    With an API key, tracking requires ``tracking:read``. Writes are deprecated and need a user token.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    @_deprecated
    def validate_address(self, body: Any) -> Any:
        """Verify an address via UPS."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsVerifyAddress"), body)

    @_deprecated
    def get_rates(self, body: Any) -> Any:
        """Get UPS rate quotes."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsRateCheck"), body)

    def track(self, params: dict[str, str]) -> Any:
        """Track a UPS shipment."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getSingleUpsTrackingDetail"), params)

    @_deprecated
    def create_pickup(self, body: Any) -> Any:
        """Create a UPS pickup."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsCreatePickup"), body)

    @_deprecated
    def cancel_pickup(self) -> Any:
        """Cancel a UPS pickup."""
        return self._http.delete(_proxy("api/v2/ShippingLabel/deleteUpsPickup"))

    @_deprecated
    def get_transit_times(self, body: Any) -> Any:
        """Get UPS transit times."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsGetTransitTimes"), body)

    @_deprecated
    def get_landed_cost(self, body: Any) -> Any:
        """Get UPS landed cost quote (international)."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsGetLandedCostQuote"), body)

    @_deprecated
    def search_locations(self, body: Any) -> Any:
        """Search UPS locations."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsSearchLocations"), body)

    @_deprecated
    def upload_document(self, body: Any) -> Any:
        """Upload paperless trade document."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsUploadPaperlessDocument"), body)

    @_deprecated
    def create_freight_shipment(self, body: Any) -> Any:
        """Create UPS freight shipment."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsCreateFreightShipment"), body)

    @_deprecated
    def get_freight_rate(self, body: Any) -> Any:
        """Get UPS freight rate."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postUpsGetFreightRate"), body)


class _FedExCarrier:
    """FedEx carrier operations via VisionSuite API proxy (V3 endpoints).

    Writes are deprecated and need a user token.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    @_deprecated
    def validate_address(self, body: Any) -> Any:
        """Validate a domestic address via FedEx."""
        return self._http.post(_proxy("api/v3/AddressValidation/postFedExValidateAndCorrectDomesticAddress"), body)

    @_deprecated
    def validate_postal_code(self, body: Any) -> Any:
        """Validate a postal code."""
        return self._http.post(_proxy("api/v3/AddressValidation/postFedExValidatePostalCode"), body)

    @_deprecated
    def get_rates(self, body: Any) -> Any:
        """Get FedEx rate and transit times."""
        return self._http.post(_proxy("api/v3/RateCalculator/postRetrieveFedExRateAndTransitTimesAsync"), body)

    @_deprecated
    def cancel_shipment(self, body: Any) -> Any:
        """Cancel a FedEx shipment."""
        return self._http.put(_proxy("api/v3/Shipping/putFedExCancelShipment"), body)

    @_deprecated
    def validate_shipment(self, body: Any) -> Any:
        """Validate a shipment (dry run)."""
        return self._http.post(_proxy("api/v3/Shipping/postFedExValidateShipment"), body)

    @_deprecated
    def track(self, body: Any) -> Any:
        """Track by tracking number."""
        return self._http.post(_proxy("api/v3/Tracking/postFedExRetrieveTrackingInfoByTrackingNumber"), body)

    @_deprecated
    def track_multi_piece(self, body: Any) -> Any:
        """Track multi-piece shipment."""
        return self._http.post(_proxy("api/v3/Tracking/postFedExRetrieveTrackingInfoForMultiPieceShipment"), body)

    @_deprecated
    def register_tracking_notification(self, body: Any) -> Any:
        """Register for tracking notifications."""
        return self._http.post(_proxy("api/v3/Tracking/postFedExRegisterForTrackingNotification"), body)

    @_deprecated
    def create_pickup(self, body: Any) -> Any:
        """Create a carrier pickup."""
        return self._http.post(_proxy("api/v3/CarrierPickup/postFedExCreateCarrierPickupRequest"), body)

    @_deprecated
    def cancel_pickup(self, body: Any) -> Any:
        """Cancel a pickup."""
        return self._http.put(_proxy("api/v3/CarrierPickup/putFedExCancelCarrierPickupRequest"), body)

    @_deprecated
    def search_locations(self, body: Any) -> Any:
        """Search valid locations."""
        return self._http.post(_proxy("api/v3/LocationSearch/postFedExSearchValidLocations"), body)

    @_deprecated
    def get_service_standards(self, body: Any) -> Any:
        """Get service standards and transit times."""
        return self._http.post(_proxy("api/v3/ServiceStandards/postFedExRetrieveServicesAndTransitTimes"), body)

    @_deprecated
    def get_freight_rate(self, body: Any) -> Any:
        """Get freight rate quote."""
        return self._http.post(_proxy("api/v3/Freight/postFedExGetFreightRateQuote"), body)

    @_deprecated
    def create_freight_shipment(self, body: Any) -> Any:
        """Create freight shipment."""
        return self._http.post(_proxy("api/v3/Freight/postFedExCreateFreightShipment"), body)

    @_deprecated
    def ground_close(self, body: Any) -> Any:
        """Ground close with documents."""
        return self._http.post(_proxy("api/v3/GroundClose/postFedExCloseWithDocuments"), body)

    @_deprecated
    def upload_trade_documents(self, body: Any) -> Any:
        """Upload trade documents."""
        return self._http.post(_proxy("api/v3/Trade/postFedExUploadTradeDocuments"), body)

    @_deprecated
    def create_open_shipment(self, body: Any) -> Any:
        """Create an open shipment."""
        return self._http.post(_proxy("api/v3/OpenShip/postFedExCreateOpenShipment"), body)

    @_deprecated
    def add_packages_to_open_shipment(self, body: Any) -> Any:
        """Add packages to an open shipment."""
        return self._http.post(_proxy("api/v3/OpenShip/postFedExAddPackagesToOpenShipment"), body)

    @_deprecated
    def confirm_open_shipment(self, body: Any) -> Any:
        """Confirm and finalize an open shipment."""
        return self._http.post(_proxy("api/v3/OpenShip/postFedExConfirmOpenShipment"), body)


class _DhlCarrier:
    """DHL carrier operations via VisionSuite API proxy (V2 endpoints).

    With an API key, address validation, service points and reference data require ``shipping:read``;
    tracking and proof of delivery require ``tracking:read``; rates and products require
    ``rates:read``. Writes are deprecated and need a user token.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def validate_address(self, params: dict[str, str]) -> Any:
        """Validate an address via DHL."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlValidateAddress"), params)

    def get_rates(self, params: dict[str, str]) -> Any:
        """Get DHL shipping rates."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlRates"), params)

    @_deprecated
    def get_multi_piece_rates(self, body: Any) -> Any:
        """Get multi-piece rates."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlMultiPieceRates"), body)

    def get_products(self, params: dict[str, str]) -> Any:
        """Get DHL products/services."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlProducts"), params)

    def track(self, params: dict[str, str]) -> Any:
        """Track a DHL shipment."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlTrackSingleShipment"), params)

    def track_multiple(self, params: dict[str, str]) -> Any:
        """Track multiple DHL shipments."""
        return self._http.get(_proxy("api/v2/ShippingLabel/getDhlTrackMultipleShipments"), params)

    @_deprecated
    def create_pickup(self, body: Any) -> Any:
        """Create a DHL pickup."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlCreatePickup"), body)

    @_deprecated
    def cancel_pickup(self) -> Any:
        """Cancel a DHL pickup."""
        return self._http.delete(_proxy("api/v2/ShippingLabel/deleteDhlPickup"))

    @_deprecated
    def calculate_landed_cost(self, body: Any) -> Any:
        """Calculate landed cost (duties/taxes)."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlCalculateLandedCost"), body)

    @_deprecated
    def screen_shipment(self, body: Any) -> Any:
        """Screen a shipment for compliance."""
        return self._http.post(_proxy("api/v2/ShippingLabel/postDhlScreenShipment"), body)

    @_deprecated
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
    """Carrier-specific operations via the legacy VisionSuite Core Services API proxy.

    Lookups (``GET``) work with a user token, or an API key that has the permission for the data they
    read: address, ZIP, city, location, service point and reference lookups require ``shipping:read``;
    tracking and proof of delivery require ``tracking:read``; delivery standards, rates and products
    require ``rates:read``. A key without the permission gets 403 ``API_KEY_SCOPE_REQUIRED``; keys
    created with the default permissions have all three. The writes are deprecated: they need a
    user token (``auth.login``), since API keys get 403 ``API_KEY_SCOPE_REQUIRED``, and they stop working
    when the proxy is retired on 2027-06-30. Use ``client.shipping`` (rates, labels, cancellation,
    tracking, address validation), ``client.pickups`` and ``client.scan_forms`` where they cover the
    call. The proxy's label-generation routes are closed (410 Gone), so they are not offered here.

    Example::

        # USPS city/state lookup
        info = client.carriers.usps.city_state_lookup("10001")

        # UPS tracking
        events = client.carriers.ups.track({"trackingNumber": "1Z999AA10123456784"})
    """

    def __init__(self, http: HttpClient) -> None:
        self.usps = _UspsCarrier(http)
        self.ups = _UpsCarrier(http)
        self.fedex = _FedExCarrier(http)
        self.dhl = _DhlCarrier(http)
