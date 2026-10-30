# FlexOps Python SDK

Official Python SDK for the [FlexOps](https://flexops.io) multi-carrier shipping platform.

## Installation

```bash
pip install flexops
```

## Quick Start

```python
from flexops import FlexOps

# API key authentication (recommended for server-to-server)
client = FlexOps(
    api_key="live_...",
    workspace_id="your-workspace-id",
)

# Get shipping rates from all carriers
rates = client.shipping.get_rates({
    "origin": {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001"},
    "destination": {"addressLine1": "456 Oak Ave", "city": "Los Angeles", "stateProvince": "CA", "postalCode": "90210"},
    "package": {"weight": 16, "weightUnit": "oz"},
})

request = {
    "carrierCode": "USPS", "serviceCode": "GROUND_ADVANTAGE",
    "origin": {"name": "Warehouse", "addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001", "countryCode": "US"},
    "destination": {"name": "Customer", "addressLine1": "456 Oak Ave", "city": "Los Angeles", "stateProvince": "CA", "postalCode": "90210", "countryCode": "US"},
    "package": {"weight": 16, "weightUnit": "oz"},
    "maximumPostageAmount": 10.25,  # Caller-approved ceiling in USD.
    # Required without an orderId. The SDK never fills it in; 0 (HazmatClassification.NONE) = not hazardous.
    "hazmatClassification": 0,
}
preview = client.shipping.create_label(request)
print(preview["quotedPostageAmount"], preview["expiresAt"])

# Run only after the caller explicitly approves this preview (within five minutes).
def purchase_approved_label(request, preview, purchase_key):
    return client.shipping.create_label(
        {**request, "confirmationToken": preview["confirmationToken"]},
        idempotency_key=purchase_key,  # Persist per purchase; reuse on retries.
    )

# Track a shipment
tracking = client.shipping.track("9400111899223456789012")
```

### Live label approval (2.0.0+)

Migration: the optional `CreateLabelRequest` model now uses `carrier_code`,
`service_code`, `origin`, `destination`, and `package`. Raw dictionaries use the
camelCase Gateway names shown below. Pass `idempotency_key` to the method, not
inside the request body. See [CHANGELOG.md](CHANGELOG.md) for model changes.

The example below requires SDK 2.0.0 or later. Version 1.0.2 does not
include the per-call idempotency argument.

For live domestic single-label requests, `maximumPostageAmount` is required: positive
USD, at most two decimal places, up to 1,000,000. Missing or invalid values return
400 `ApprovalRequired`. Omitting `confirmationToken` returns a raw 200 preview
(`status`, `quotedPostageAmount`, `maximumPostageAmount`, `currency`, `expiresAt`,
`confirmationToken`). After explicit approval, resubmit the same shipment and ceiling
with the token and a unique per-purchase `Idempotency-Key` header. The token expires
after five minutes. A successful purchase returns the raw 201 label, including
`labelId`, `trackingNumber`, `carrierCode`, and `labelData`, without a `data` wrapper.

Keep the same key and request across retries. An uncertain outcome needs reconciliation;
do not start another purchase with a new key. An expired approval returns 409
`ApprovalExpired`; obtain and explicitly approve a fresh preview when no purchase is
unresolved. The ceiling bounds postage authorization, not later adjustments or separate
fees. Sandbox keys follow the same approval and buy no postage; batch, return, and raw carrier routes have
separate contracts. The SDK never automatically confirms a preview.

## Authentication

### API Key (recommended)

```python
client = FlexOps(api_key="live_...", workspace_id="your-workspace-id")
```

### Email / Password

```python
client = FlexOps(base_url="https://gateway.flexops.io")
client.auth.login("user@example.com", "password")
client.workspace_id = "your-workspace-id"
```

## Carrier-Specific Operations

`client.carriers` reaches USPS, UPS, FedEx and DHL through the legacy API proxy. The lookups (`GET`)
work with a user token, or an API key that has the permission for the data: `shipping:read` for
address, ZIP, city, location, service point and reference lookups; `tracking:read` for tracking and
proof of delivery; `rates:read` for delivery standards, rates and products. Without it the Gateway
returns 403 `API_KEY_SCOPE_REQUIRED`. The writes are deprecated: each call raises a
`DeprecationWarning`, they need a user token (`auth.login`) because API keys get 403
`API_KEY_SCOPE_REQUIRED`, and they stop working when the proxy is retired on 2027-06-30. The proxy's
label-generation routes are closed (410 Gone) and are not offered.

Native replacements: `client.shipping` (rates, labels, cancellation, tracking, address validation),
`client.pickups` (carrier pickups), `client.scan_forms` (USPS scan forms) and `client.hs_codes`
(landed cost).

```python
# USPS city/state lookup (user token, or API key with shipping:read)
info = client.carriers.usps.city_state_lookup("10001")

# UPS tracking
events = client.carriers.ups.track({"trackingNumber": "1Z999AA10123456784"})

# Deprecated proxy write: user token only
client.auth.login("user@example.com", "password")
rates = client.carriers.fedex.get_rates({...})
```

## Recurring Shipments, Report Schedules and Email Templates

Reads work with any API key or a user token. Writes need a user token or an API key granted the
resource's scope: `recurring-shipments:write`, `report-schedules:write` or `email-templates:write`.
A key without it gets 403 `API_KEY_SCOPE_REQUIRED` naming `requiredScopes`.

```python
from flexops import RecurrenceInterval, TrackingEmailEvent

schedule = client.recurring_shipments.create({
    "name": "Weekly restock", "interval": RecurrenceInterval.WEEKLY,
    "presetId": preset_id, "addressId": address_id, "firstRunUtc": "2026-11-02T14:00:00Z",
})
client.email_templates.upsert({
    "eventType": TrackingEmailEvent.DELIVERED,
    "subjectTemplate": "Your order was delivered",
    "htmlBodyTemplate": "<p>Tracking {{trackingNumber}} was delivered.</p>",
})
reports = client.report_schedules.list()["data"]  # report schedules use the envelope
```

## Retries and Idempotency

Every `POST`, `PUT` and `PATCH` sends an `Idempotency-Key` header: the key you pass (for example
`idempotency_key=` on `shipping.create_label`, `insurance.purchase`, `carbon_offsets.purchase` and
`recurring_shipments.trigger`),
or one the SDK generates for that call. The same key is sent on every retry of the call, so the
Gateway replays a write it already finished instead of charging twice.

- `GET` retries on a dropped connection, a timeout, 429, 500, 502, 503 and 504.
- `POST`, `PUT` and `PATCH` retry on a dropped connection, a timeout, 429, 502, 503, 504 and 409
  `IDEMPOTENCY_CONFLICT`, never on 500 (the Gateway does not replay a 500, so a retry would run the
  write again).
- A key reused with a different request gets 422 `IDEMPOTENCY_KEY_REUSED` and is not retried.
- `DELETE` retries only on 429.

A generated key lives only for one call. To retry a purchase later, after the call has returned,
persist your own key with it and pass it again. A response with no body (204) returns `None`.

## Workspace Roles

Roles are sent as the Gateway numbers. Pass a `WorkspaceRole`, its name or its number:

```python
from flexops import WorkspaceRole

client.workspaces.invite_member("ops@example.com", WorkspaceRole.ADMIN)  # or "Admin", or 1
client.workspaces.update_member_role(user_id, "Member")
```

## Webhook Subscriptions

Managing webhooks needs a signed-in user's access token. The Gateway refuses API keys on every webhook
route, reads included (`list` and `list_delivery_logs` as well as `create`, `update`, `delete`,
`rotate_secret` and `test`), with 403 `SIGNED_IN_USER_REQUIRED`, whatever the key's scopes; the SDK
raises `FlexOpsError` with that `code`. Reads are refused too because webhook delivery logs carry each
delivery's payload (order and customer data). A client with an API key sends the key even when an access
token is also set, so use a client created without `api_key`. Verifying deliveries (below) makes no
request and needs no credentials.

```python
from flexops import FlexOps, WebhookEventType

# Sign in as a user (or pass access_token=); an API key gets 403 SIGNED_IN_USER_REQUIRED here.
client = FlexOps(workspace_id="your-workspace-id")
client.auth.login("user@example.com", "password")

# Leave events out to receive every event.
webhook = client.webhooks.create(
    "https://your-app.com/webhooks/flexops",
    [WebhookEventType.LABEL_CREATED, WebhookEventType.LABEL_CANCELED, WebhookEventType.BATCH_COMPLETED],
)
signing_secret = webhook["data"]["secret"]  # returned only on create; store it
```

FlexOps sends these events, named exactly as below. Names are PascalCase and matched exactly, so a
name like `label.created` would never match; `create` and `update` raise `ValueError` for unknown names.

| Event | Sent when |
|---|---|
| `LabelCreated` | A live label is purchased (sandbox labels send nothing) |
| `LabelCanceled` | A live label is voided |
| `BatchCompleted` | A batch label job finishes |
| `TrackingUpdated` | A USPS tracking scan arrives (USPS push-tracking pilot workspaces only) |
| `TrackingDelivered` | A USPS package is delivered (USPS push-tracking pilot workspaces only) |

## Webhook Verification

Each delivery is a `POST` whose body is the event data itself (there is no `{"type", "data"}`
envelope). The headers carry the rest:

| Header | Value |
|---|---|
| `X-FlexOps-Event` | Event name, e.g. `LabelCreated`; `test` for a test delivery |
| `X-FlexOps-Event-Id` | Event ID; use it to ignore retried duplicates |
| `X-FlexOps-Timestamp` | Unix seconds when the delivery was signed |
| `X-FlexOps-Signature` | `sha256=` + hex HMAC-SHA256 of `{timestamp}.{raw body}`, keyed with your `whsec_...` secret |
| `X-FlexOps-Delivery` | Delivery attempt ID |

Verify against the raw body bytes; re-serialized JSON does not reproduce what was signed.

```python
import json
import os

from flask import Flask, request

from flexops import WebhooksResource

app = Flask(__name__)


@app.post("/webhooks/flexops")
def flexops_webhook():
    raw_body = request.get_data()  # bytes, exactly as received
    if not WebhooksResource.verify_signature(
        raw_body,
        request.headers.get("X-FlexOps-Signature"),
        os.environ["FLEXOPS_WEBHOOK_SECRET"],
        timestamp=request.headers.get("X-FlexOps-Timestamp"),  # rejected if more than 300 s from now
    ):
        return "Invalid signature", 401

    event_type = request.headers["X-FlexOps-Event"]  # "LabelCreated", "TrackingUpdated", "test", ...
    data = json.loads(raw_body)  # the event data; no envelope
    # Process the event...
    return "", 200
```

`timestamp` is keyword-only and required. Pass `tolerance=` (seconds) to change the 300 second window.

## Curl Quickstart

Every SDK method is a thin wrapper around the FlexOps REST API. If you want to verify the API before committing to the SDK — or you're integrating from a language we don't ship a SDK for — these curl invocations hit the same endpoints:

```bash
# Shop rates across all connected carriers
curl -X POST https://gateway.flexops.io/api/shipping/rates \
  -H "X-API-Key: live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001", "countryCode": "US"},
    "destination": {"addressLine1": "456 Oak Ave", "city": "Los Angeles", "stateProvince": "CA", "postalCode": "90210", "countryCode": "US"},
    "package": {"weight": 16, "weightUnit": "oz"}
  }'

# Preview a live label; this does not purchase it.
# hazmatClassification 0 = not hazardous; required when there is no orderId.
curl -X POST https://gateway.flexops.io/api/shipping/labels \
  -H "X-API-Key: live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "carrierCode": "USPS", "serviceCode": "GROUND_ADVANTAGE",
    "origin": {"name": "Warehouse", "addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001", "countryCode": "US"},
    "destination": {"name": "Customer", "addressLine1": "456 Oak Ave", "city": "Los Angeles", "stateProvince": "CA", "postalCode": "90210", "countryCode": "US"},
    "package": {"weight": 16, "weightUnit": "oz"},
    "maximumPostageAmount": 10.25,
    "hazmatClassification": 0
  }'

# After explicit approval, resend the same body with confirmationToken from
# the preview and an Idempotency-Key header unique to this purchase.
# See the SDK example above; retain that key for retries.

# Track a shipment
curl https://gateway.flexops.io/api/shipping/track/9400111899223456789012 \
  -H "X-API-Key: live_..."

# Cancel (void) a label
curl -X DELETE "https://gateway.flexops.io/api/shipping/labels/{labelId}?carrierCode=USPS" \
  -H "X-API-Key: live_..."
```

Use a `test_...` key instead of `live_...` to hit the sandbox environment; mock carriers respond, no real charges, no real labels.

## Resources

| Resource | Methods | Description |
|----------|---------|-------------|
| `client.auth` | 3 | Login, token refresh, logout |
| `client.workspaces` | 6 | Workspaces you belong to, membership |
| `client.shipping` | 15 | Rate shopping, labels, tracking, address validation, batch |
| `client.carriers` | 62 | USPS, UPS, FedEx and DHL via the legacy proxy (writes deprecated) |
| `client.webhooks` | 8 | Subscription CRUD, test events, signature verification |
| `client.wallet` | 1 | Balance |
| `client.insurance` | 5 | Quotes, policies, claims |
| `client.returns` | 5 | RMA creation, labels, receiving |
| `client.analytics` | 15 | Shipments, orders, carrier analytics (API keys need each method's read permission) |
| `client.orders` | 10 | Order reads (API keys need `orders:read`) |
| `client.inventory` | 3 | Warehouse inventory reads (API keys need `inventory:read`) |
| `client.pickups` | 4 | Carrier pickup scheduling |
| `client.scan_forms` | 3 | USPS scan forms |
| `client.rules` | 7 | Shipping automation rules |
| `client.carbon_offsets` | 7 | Carbon offset quotes, purchases, settings |
| `client.hs_codes` | 3 | HS code search and landed cost |
| `client.recurring_shipments` | 8 | Recurring shipment schedules |
| `client.report_schedules` | 6 | Scheduled reports |
| `client.email_templates` | 5 | Shipment notification email templates |

`client.analytics`, `client.orders` and `client.inventory` read through the legacy API proxy. With an API
key they need the permission for the data they read: `orders:read` for orders, `inventory:read` for
inventory, and for analytics the permission named on each method (`shipping:read`, `inventory:read`,
`orders:read` or `returns:read`). A key without it gets 403 `API_KEY_SCOPE_REQUIRED`. Keys created with the
default permissions have all of these.

API keys, wallet funding and account management are portal features and are not part of the SDK.

## Configuration

```python
client = FlexOps(
    base_url="https://gateway.flexops.io",  # API base URL
    api_key="live_...",                  # API key auth
    workspace_id="your-workspace-id",    # Default workspace
    timeout=30.0,                        # Request timeout (seconds)
    headers={"X-Custom": "value"},       # Custom headers
    retry={                              # Retry configuration
        "max_retries": 3,
        "base_delay": 1.0,
    },
)
```

## Requirements

- Python 3.10+
- `requests` >= 2.31
- `pydantic` >= 2.0

## License

MIT © FlexOps, LLC. See [LICENSE](LICENSE) for full text.
