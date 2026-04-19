# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from typing import Generic, Literal, TypeVar

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
    access_token: str
    refresh_token: str
    expires_at: str
    user_id: str


class RegisterRequest(_CamelModel):
    email: str
    password: str
    first_name: str
    last_name: str
    company_name: str | None = None


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------


class Workspace(_CamelModel):
    id: str
    name: str
    slug: str
    plan_id: str
    owner_id: str
    is_active: bool
    monthly_label_limit: int
    labels_used_this_month: int
    user_limit: int
    created_at: str


class CreateWorkspaceRequest(_CamelModel):
    name: str
    plan_id: str | None = None


class WorkspaceMember(_CamelModel):
    user_id: str
    email: str
    role: Literal["Owner", "Admin", "Member", "Guest"]
    joined_at: str


# ---------------------------------------------------------------------------
# Shipping - Rate Shopping
# ---------------------------------------------------------------------------


class RateRequest(_CamelModel):
    from_zip: str
    to_zip: str
    weight: float
    weight_unit: Literal["oz", "lb", "g", "kg"] | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    dimension_unit: Literal["in", "cm"] | None = None
    package_type: str | None = None
    carriers: list[str] | None = None


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


class CreateLabelRequest(_CamelModel):
    carrier: str
    service: str
    from_address: Address
    to_address: Address
    parcel: Parcel
    return_label: bool | None = None
    label_format: Literal["PDF", "PNG", "ZPL"] | None = None
    idempotency_key: str | None = None


class Label(_CamelModel):
    label_id: str
    tracking_number: str
    carrier: str
    service: str
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


class AddressValidationResult(_CamelModel):
    is_valid: bool
    corrected_address: Address | None = None
    messages: list[str] | None = None


# ---------------------------------------------------------------------------
# Batch Labels
# ---------------------------------------------------------------------------


class BatchLabelRequest(_CamelModel):
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


class WebhookSubscription(_CamelModel):
    id: str
    url: str
    events: list[str]
    is_active: bool
    secret: str
    created_at: str


class CreateWebhookRequest(_CamelModel):
    url: str
    events: list[str]


# ---------------------------------------------------------------------------
# Wallet / Billing
# ---------------------------------------------------------------------------


class WalletBalance(_CamelModel):
    balance: float
    currency: str
    auto_reload_enabled: bool
    auto_reload_threshold: float | None = None
    auto_reload_amount: float | None = None


# ---------------------------------------------------------------------------
# Insurance
# ---------------------------------------------------------------------------


class InsuranceQuote(_CamelModel):
    provider: str
    premium: float
    coverage: float
    currency: str


class InsurancePolicy(_CamelModel):
    policy_id: str
    provider: str
    tracking_number: str
    coverage: float
    premium: float
    status: str


# ---------------------------------------------------------------------------
# Returns / RMA
# ---------------------------------------------------------------------------


class ReturnItem(_CamelModel):
    sku: str
    quantity: int
    reason: str | None = None


class ReturnRequest(_CamelModel):
    order_id: str
    reason: str
    items: list[ReturnItem]


class ReturnAuthorization(_CamelModel):
    rma_id: str
    status: str
    return_label: Label | None = None
    created_at: str


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------


class ApiKeyInfo(_CamelModel):
    id: str
    name: str
    prefix: str
    scopes: list[str]
    last_used_at: str | None = None
    expires_at: str | None = None
    created_at: str


class CreateApiKeyRequest(_CamelModel):
    name: str
    scopes: list[str] | None = None
    expires_in_days: int | None = None


class CreateApiKeyResponse(_CamelModel):
    id: str
    key: str
    name: str
    prefix: str


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
    is_active: bool
    priority: int
    conditions: list[RuleCondition]
    actions: list[RuleAction]


# ---------------------------------------------------------------------------
# Pickups
# ---------------------------------------------------------------------------


class PickupRequest(_CamelModel):
    carrier: str
    pickup_date: str
    ready_time: str
    close_time: str
    address: Address
    package_count: int
    total_weight: float


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
