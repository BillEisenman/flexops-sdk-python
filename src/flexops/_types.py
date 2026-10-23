# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------------------
# Client Configuration
# ---------------------------------------------------------------------------


class RetryConfig(_CamelModel):
    max_retries: int = 3
    base_delay: float = 1.0
    retryable_status_codes: list[int] = [429, 500, 502, 503, 504]


class FlexOpsConfig(_CamelModel):
    base_url: str = "https://gateway.flexops.io"
    access_token: str | None = None
    api_key: str | None = None
    workspace_id: str | None = None
    timeout: float = 30.0
    headers: dict[str, str] | None = None
    retry: RetryConfig | None = None


# ---------------------------------------------------------------------------
# API Response Wrapper
# ---------------------------------------------------------------------------


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None
    errors: list[str] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class LoginRequest(_CamelModel):
    email: str
    password: str


class LoginResponse(_CamelModel):
    """The ``data`` of ``auth.login()`` and ``auth.refresh_token()``. ``token`` is the access token."""

    token: str | None = None
    refresh_token: str | None = None
    expires_at: str
    user_id: str
    email: str
    first_name: str
    last_name: str
    roles: list[str] = []
    requires_two_factor: bool = False
    two_factor_token: str | None = None
    two_factor_method: str | None = None


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------


class WorkspaceRole(IntEnum):
    """A member's role, sent and returned as the Gateway ``WorkspaceRole`` number."""

    OWNER = 0
    ADMIN = 1
    MEMBER = 2
    # A store merchant in a workspace another party (such as a 3PL) operates.
    MERCHANT = 3


class WorkspaceSummary(_CamelModel):
    """One entry of ``workspaces.list()``."""

    id: str
    name: str
    slug: str
    my_role: int
    plan_id: str
    member_count: int
    is_creator: bool
    product_type: str | None = None
    entitlements: list[Any] = []


class Workspace(_CamelModel):
    """The ``data`` of ``workspaces.get()``. Status fields are Gateway enum numbers."""

    id: str
    name: str
    slug: str
    domain: str | None = None
    plan_id: str
    status: int
    subscription_status: int
    user_limit: int
    current_user_count: int
    monthly_label_limit: int
    labels_used_this_month: int
    is_trialing: bool
    trial_expires_at: str | None = None
    my_role: int
    can_manage_members: bool
    can_manage_billing: bool
    created_at: str
    entitlements: list[Any] = []


class WorkspaceMember(_CamelModel):
    """A member in ``workspaces.list_members()``. ``role`` is a ``WorkspaceRole`` number."""

    membership_id: str
    user_id: str
    email: str
    name: str | None = None
    role: int
    status: int
    joined_at: str
    is_creator: bool
    is_deactivated: bool
    store_scope: int
    store_connection_ids: list[str] = []


class WorkspaceMemberList(_CamelModel):
    """The ``data`` of ``workspaces.list_members()``: members and pending invites, not a bare list."""

    members: list[WorkspaceMember]
    pending_invites: list[dict[str, Any]] = []
    user_limit: int
    active_count: int
    can_invite_more: bool


# ---------------------------------------------------------------------------
# Shipping - Rate Shopping
# ---------------------------------------------------------------------------


class ShippingAddress(_CamelModel):
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    country_code: str = "US"
    name: str | None = None
    company: str | None = None
    address_line2: str | None = None
    phone: str | None = None
    email: str | None = None
    is_residential: bool | None = None


class ShippingPackage(_CamelModel):
    weight: float
    weight_unit: Literal["oz", "lb", "g", "kg"] = "oz"
    length: float | None = None
    width: float | None = None
    height: float | None = None
    dimension_unit: Literal["in", "cm"] = "in"
    predefined_package: str | None = None


class HazmatClassification(IntEnum):
    """USPS HAZMAT classification, sent as the Gateway ``HazmatClassification`` number.

    There is no default: leave ``hazmat_classification`` unset when you have no answer, or send
    ``HazmatClassification.NONE`` (0) to declare that the parcel holds no dangerous goods.
    """

    NONE = 0
    LIMITED_QUANTITY = 1
    LITHIUM_BATTERY_CONTAINED_IN_EQUIPMENT = 2
    LITHIUM_BATTERY_PACKED_WITH_EQUIPMENT = 3
    LITHIUM_BATTERY_STANDALONE = 4
    OTHER_RESTRICTED = 5
    LITHIUM_BATTERY_USED_DEVICE = 6


class RateRequest(_CamelModel):
    origin: ShippingAddress
    destination: ShippingAddress
    package: ShippingPackage
    carriers: list[str] | None = None
    service_levels: list[str] | None = None
    ship_date: str | None = None
    include_insurance: bool = False
    declared_value: float | None = None
    currency: str = "USD"
    # Declared HAZMAT class, so quotes match what the label route will accept. Sent only when set.
    hazmat_classification: HazmatClassification | None = None


class ShippingRate(_CamelModel):
    carrier: str
    service: str
    rate: float
    currency: str
    estimated_days: int
    delivery_date: str | None = None


# ---------------------------------------------------------------------------
# Shipping - Labels
# ---------------------------------------------------------------------------


class Address(_CamelModel):
    name: str
    company: str | None = None
    street1: str
    street2: str | None = None
    city: str
    state: str
    zip: str
    country: str
    phone: str | None = None
    email: str | None = None


class Parcel(_CamelModel):
    weight: float
    weight_unit: Literal["oz", "lb", "g", "kg"] | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    dimension_unit: Literal["in", "cm"] | None = None


class CustomsItem(_CamelModel):
    """Value and weight_oz describe one unit, not the entire line."""
    description: str
    quantity: int
    value: float
    weight_oz: float
    hs_code: str | None = None
    origin_country: str


class CustomsDeclaration(_CamelModel):
    contents_type: str = "merchandise"
    contents_explanation: str | None = None
    non_delivery_option: Literal["return", "abandon"] = "return"
    currency: Literal["USD"] = "USD"
    declared_value: float
    aes_itn: str
    invoice_number: str | None = None
    license_number: str | None = None
    certificate_number: str | None = None
    restriction_type: str | None = None
    restriction_comments: str | None = None
    items: list[CustomsItem]


class CreateLabelRequest(_CamelModel):
    order_id: int | None = None
    ship_date: str | None = None
    declared_value: float | None = None
    customs_declaration: CustomsDeclaration | None = None
    rate_indicator: str | None = None
    carrier_code: str
    service_code: str
    origin: ShippingAddress
    destination: ShippingAddress
    package: ShippingPackage
    maximum_postage_amount: float | None = None
    confirmation_token: str | None = None
    label_format: Literal["PDF", "PNG", "ZPL"] | None = None
    # Declared HAZMAT class. A label without an order_id must declare one (HazmatClassification.NONE
    # for an ordinary parcel). Sent only when set; the SDK never fills it in.
    hazmat_classification: HazmatClassification | None = None


class LabelPurchasePreview(_CamelModel):
    status: Literal["Preview"]
    quoted_postage_amount: float
    maximum_postage_amount: float
    currency: str
    expires_at: str
    confirmation_token: str


class Label(_CamelModel):
    label_id: str
    tracking_number: str
    carrier_code: str
    currency: str = "USD"
    label_data: str
    label_format: str
    rate: float
    created_at: str


# ---------------------------------------------------------------------------
# Shipping - Tracking
# ---------------------------------------------------------------------------


class TrackingEvent(_CamelModel):
    timestamp: str
    status: str
    description: str
    location: str | None = None


class TrackingInfo(_CamelModel):
    tracking_number: str
    carrier: str
    status: str
    status_detail: str
    estimated_delivery: str | None = None
    events: list[TrackingEvent]


# ---------------------------------------------------------------------------
# Shipping - Address Validation
# ---------------------------------------------------------------------------


class SuggestedAddress(_CamelModel):
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str


class AddressValidationResult(_CamelModel):
    """The Gateway result of ``shipping.validate_address``.

    ``validation_unavailable`` means no carrier could check the address; it is not a rejection.
    """

    is_valid: bool
    suggested_address: SuggestedAddress | None = None
    is_residential: bool | None = None
    warnings: list[str] = []
    validated_by: str | None = None
    validation_unavailable: bool = False
    checked_at: str | None = None


# ---------------------------------------------------------------------------
# Batch Labels
# ---------------------------------------------------------------------------


class BatchLabelItem(_CamelModel):
    """One order in a batch: the Gateway BatchLabelItemRequest. Addresses come from the order."""
    order_id: int
    order_number: str | None = None
    package_weight_in_ounces: float
    package_length_in_inches: float
    package_width_in_inches: float
    package_height_in_inches: float
    carrier_code: str | None = None
    service_code: str | None = None
    delivery_confirmation_required: bool = False
    signature_confirmation_required: bool = False
    insurance_coverage_requested: bool = False
    insured_value: float | None = None
    label_format: str = "PDF"
    ship_date: str | None = None
    # What the parcel holds. Sent only when set. Batch labels cannot carry HAZMAT yet, so the
    # Gateway accepts only HazmatClassification.NONE (0) or nothing and refuses any other class
    # with 400 HazmatNotSupported; buy HAZMAT labels one at a time with shipping.create_label.
    hazmat_classification: HazmatClassification | None = None


class CreateBatchLabelRequest(_CamelModel):
    """The Gateway CreateBatchLabelRequest for shipping.create_batch and preview_batch."""
    items: list[BatchLabelItem]
    callback_url: str | None = None
    dry_run: bool = False


class MultiPackageDetail(_CamelModel):
    """One box in a multi-package shipment: the Gateway PackageDetail.

    Weight is in ounces (0.1 to 999999) and each dimension in inches (0.1 to 999).
    ``insured_value`` (USD) needs ``insurance_coverage_requested``; left out, the order value is insured.
    """
    weight_in_ounces: float
    length_in_inches: float
    width_in_inches: float
    height_in_inches: float
    delivery_confirmation_required: bool = False
    signature_confirmation_required: bool = False
    insurance_coverage_requested: bool = False
    insured_value: float | None = None
    # Your label for the box, up to 100 characters (for example "Box 1 of 3").
    package_reference: str | None = None


class MultiPackageShipmentRequest(_CamelModel):
    """The Gateway MultiPackageShipmentRequest for shipping.create_multi_package.

    One order shipped in 1 to 99 boxes with the same carrier and service; the addresses come from
    the order. Multi-package labels cannot carry HAZMAT yet, so ``hazmat_classification`` accepts only
    ``HazmatClassification.NONE`` or nothing (the Gateway refuses any other class with 400
    ``HazmatNotSupported``); buy HAZMAT labels one at a time with ``shipping.create_label``.

    ``maximum_postage_amount`` is required: the most the whole shipment may cost, in USD (positive, at
    most two decimals). The Gateway refuses to buy a box that would take the total above it, so you never
    pay more: a box priced above what is left reports ``PriceCeilingExceeded``, and once the amount is
    used up the remaining boxes report ``PriceCeilingReached`` and are not bought. Boxes already bought
    stay bought. A missing or invalid value is 400 ``ApprovalRequired``.
    """
    order_id: int
    carrier_code: str
    service_code: str | None = None
    label_format: str | None = None
    ship_date: str | None = None
    hazmat_classification: Literal[HazmatClassification.NONE] | None = None
    maximum_postage_amount: float
    packages: list[MultiPackageDetail]


class MultiPackageLabelResult(_CamelModel):
    """One box's outcome: the Gateway PackageLabelResult. ``error_code`` ``OutcomeUnknown`` means a label may exist."""
    package_index: int
    package_reference: str | None = None
    tracking_number: str | None = None
    rate: float | None = None
    success: bool
    error_message: str | None = None
    error_code: str | None = None


class MultiPackageShipmentResponse(_CamelModel):
    """The Gateway MultiPackageShipmentResponse (the envelope's ``data``)."""
    order_id: int
    carrier_code: str | None = None
    total_packages: int
    successful_packages: int
    failed_packages: int
    total_cost: float
    labels: list[MultiPackageLabelResult] = []


class BatchLabelRequest(_CamelModel):
    """Deprecated: does not match the Gateway batch body. Use CreateBatchLabelRequest."""
    items: list[CreateLabelRequest]
    idempotency_key: str | None = None


class BatchLabelJob(_CamelModel):
    job_id: str
    status: Literal["Queued", "Processing", "Completed", "Failed"]
    total_items: int
    completed_items: int
    failed_items: int
    created_at: str


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrderItem(_CamelModel):
    sku: str
    name: str
    quantity: int
    unit_price: float


class Order(_CamelModel):
    order_number: str
    status: str
    customer_name: str | None = None
    items: list[OrderItem]
    shipping_address: Address
    created_at: str


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


class WebhookEventType(str, Enum):
    """Event names FlexOps sends in ``X-FlexOps-Event`` and matches subscriptions against.

    Names are PascalCase and matched exactly: a dotted name such as ``label.created`` matches
    nothing. ``TRACKING_UPDATED`` and ``TRACKING_DELIVERED`` are sent only to workspaces in the
    USPS push-tracking pilot.
    """

    LABEL_CREATED = "LabelCreated"
    LABEL_CANCELED = "LabelCanceled"
    BATCH_COMPLETED = "BatchCompleted"
    TRACKING_UPDATED = "TrackingUpdated"
    TRACKING_DELIVERED = "TrackingDelivered"


class WebhookSubscription(_CamelModel):
    """A webhook subscription as the Gateway returns it."""

    id: str
    url: str
    description: str | None = None
    # Subscribed event names, comma-separated, or "*" for every event.
    event_types: str
    # "Active", "Paused" or "Disabled".
    status: str
    consecutive_failures: int = 0
    created_at: str
    updated_at: str | None = None
    # The whsec_... signing secret. Returned only when the subscription is created.
    secret: str | None = None


class CreateWebhookRequest(_CamelModel):
    """The Gateway create body. ``event_types`` is comma-separated with no spaces; omit it for every event."""

    url: str
    description: str | None = None
    event_types: str | None = None


# ---------------------------------------------------------------------------
# Wallet / Billing
# ---------------------------------------------------------------------------


class WalletBalance(_CamelModel):
    """The bare response of ``wallet.get_balance()``."""

    has_wallet: bool
    balance_cents: int
    balance: float


# ---------------------------------------------------------------------------
# Insurance
# ---------------------------------------------------------------------------


class InsuranceQuote(_CamelModel):
    """The ``data`` of ``insurance.get_quote()``."""

    declared_value: float
    coverage_amount: float
    premium: float
    coverage_tier: str
    carrier_code: str
    coverage_days: int = 30
    provider: str


class InsurancePolicy(_CamelModel):
    """The ``data`` of ``insurance.purchase()`` and ``insurance.void()``."""

    policy_id: str
    tracking_number: str
    carrier_code: str
    declared_value: float
    coverage_amount: float
    premium: float
    status: str
    coverage_tier: str | None = None
    purchased_at: str
    expires_at: str
    cancelled_at: str | None = None
    provider: str | None = None
    provider_reference: str | None = None
    is_sandbox: bool = False


# ---------------------------------------------------------------------------
# Returns / RMA
# ---------------------------------------------------------------------------


class ReturnItem(_CamelModel):
    sku: str
    quantity: int
    reason: str | None = None


class ReturnRequest(_CamelModel):
    """The Gateway ``CreateRmaRequest`` body of ``returns.create``."""

    order_id: int
    order_number: str | None = None
    reason: str
    items: list[ReturnItem]
    notes: str | None = None
    customer_email: str | None = None
    reason_id: int | None = None


class ReturnAuthorization(_CamelModel):
    rma_id: str
    status: str
    return_label: Label | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class ShipmentsTrend(_CamelModel):
    date: str
    count: int
    total_cost: float


class CarrierSummary(_CamelModel):
    carrier: str
    label_count: int
    total_cost: float
    average_cost: float


# ---------------------------------------------------------------------------
# Automation Rules
# ---------------------------------------------------------------------------


class RuleCondition(_CamelModel):
    field: str
    operator: str
    value: str
    group: int | None = None


class RuleAction(_CamelModel):
    type: str
    value: str


class ShippingRule(_CamelModel):
    id: str
    name: str
    priority: int
    is_enabled: bool
    warehouse_id: str | None = None
    conditions: list[RuleCondition]
    actions: list[RuleAction]


# ---------------------------------------------------------------------------
# Recurring Shipments, Report Schedules, Email Templates
# ---------------------------------------------------------------------------


class RecurrenceInterval(IntEnum):
    """How often a recurring shipment runs. ``CUSTOM`` uses ``cronExpression``."""

    DAILY = 0
    WEEKLY = 1
    BIWEEKLY = 2
    MONTHLY = 3
    CUSTOM = 4


class ReportFormat(IntEnum):
    CSV = 0
    JSON = 1


class ReportFrequency(IntEnum):
    """``WEEKLY`` uses ``dayOfWeek`` (Sunday 0); ``MONTHLY`` uses ``dayOfMonth`` (1-28)."""

    DAILY = 0
    WEEKLY = 1
    MONTHLY = 2


class TrackingEmailEvent(IntEnum):
    """The tracking event an email template is sent for."""

    LABEL_CREATED = 0
    IN_TRANSIT = 1
    OUT_FOR_DELIVERY = 2
    DELIVERED = 3
    EXCEPTION = 4
    RETURN_TO_SENDER = 5


# ---------------------------------------------------------------------------
# Pickups
# ---------------------------------------------------------------------------


class PickupRequest(_CamelModel):
    """The Gateway ``SchedulePickupRequest`` body of ``pickups.schedule``."""

    carrier_code: str
    pickup_date: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str | None = None
    package_count: int = 1
    total_weight_oz: float | None = None
    special_instructions: str | None = None
    ready_time: str | None = None
    close_time: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None


class PickupConfirmation(_CamelModel):
    confirmation_number: str
    carrier: str
    pickup_date: str
    status: str


# ---------------------------------------------------------------------------
# Scan Forms
# ---------------------------------------------------------------------------


class ScanFormRequest(_CamelModel):
    tracking_numbers: list[str]


class ScanForm(_CamelModel):
    scan_form_id: str
    form_data: str
    tracking_numbers: list[str]
    created_at: str
