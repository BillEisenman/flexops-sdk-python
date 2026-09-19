# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

"""Official FlexOps Platform Python SDK.

Usage::

    from flexops import FlexOps

    client = FlexOps(api_key="fxk_live_...", workspace_id="ws_abc123")
    rates = client.shipping.get_rates({
        "origin": {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001"},
        "destination": {"addressLine1": "456 Oak Ave", "city": "Los Angeles",
                            "stateProvince": "CA", "postalCode": "90210"},
        "package": {"weight": 16, "weightUnit": "oz"},
    })
"""

from ._errors import FlexOpsAuthError, FlexOpsError, FlexOpsRateLimitError
from ._types import (
    Address,
    AddressValidationResult,
    ApiKeyInfo,
    ApiResponse,
    BatchLabelJob,
    BatchLabelRequest,
    CarrierSummary,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    CreateLabelRequest,
    CreateWebhookRequest,
    CreateWorkspaceRequest,
    FlexOpsConfig,
    InsurancePolicy,
    InsuranceQuote,
    Label,
    LabelPurchasePreview,
    LoginRequest,
    LoginResponse,
    Order,
    OrderItem,
    PaginatedResponse,
    Parcel,
    PickupConfirmation,
    PickupRequest,
    RateRequest,
    RegisterRequest,
    RetryConfig,
    ReturnAuthorization,
    ReturnItem,
    ReturnRequest,
    RuleAction,
    RuleCondition,
    ScanForm,
    ScanFormRequest,
    ShipmentsTrend,
    ShippingAddress,
    ShippingPackage,
    ShippingRate,
    ShippingRule,
    TrackingEvent,
    TrackingInfo,
    WalletBalance,
    WebhookSubscription,
    Workspace,
    WorkspaceMember,
)
from .client import FlexOps
from .resources import (
    AnalyticsResource,
    ApiKeysResource,
    AuthResource,
    CarriersResource,
    InsuranceResource,
    InventoryResource,
    OrdersResource,
    PickupsResource,
    ReturnsResource,
    RulesResource,
    ScanFormsResource,
    ShippingResource,
    WalletResource,
    WebhooksResource,
    WorkspacesResource,
)

__version__ = "2.0.0"

__all__ = [
    # Client
    "FlexOps",
    # Errors
    "FlexOpsError",
    "FlexOpsAuthError",
    "FlexOpsRateLimitError",
    # Config
    "FlexOpsConfig",
    "RetryConfig",
    # Types
    "ApiResponse",
    "PaginatedResponse",
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "Workspace",
    "CreateWorkspaceRequest",
    "WorkspaceMember",
    "RateRequest",
    "ShippingAddress",
    "ShippingPackage",
    "ShippingRate",
    "CreateLabelRequest",
    "Label",
    "LabelPurchasePreview",
    "Address",
    "Parcel",
    "TrackingInfo",
    "TrackingEvent",
    "AddressValidationResult",
    "BatchLabelRequest",
    "BatchLabelJob",
    "Order",
    "OrderItem",
    "WebhookSubscription",
    "CreateWebhookRequest",
    "WalletBalance",
    "InsuranceQuote",
    "InsurancePolicy",
    "ReturnRequest",
    "ReturnItem",
    "ReturnAuthorization",
    "ApiKeyInfo",
    "CreateApiKeyRequest",
    "CreateApiKeyResponse",
    "ShipmentsTrend",
    "CarrierSummary",
    "ShippingRule",
    "RuleCondition",
    "RuleAction",
    "PickupRequest",
    "PickupConfirmation",
    "ScanFormRequest",
    "ScanForm",
    # Resources
    "AuthResource",
    "WorkspacesResource",
    "ShippingResource",
    "CarriersResource",
    "WebhooksResource",
    "WalletResource",
    "InsuranceResource",
    "ReturnsResource",
    "ApiKeysResource",
    "AnalyticsResource",
    "OrdersResource",
    "InventoryResource",
    "PickupsResource",
    "ScanFormsResource",
    "RulesResource",
]
