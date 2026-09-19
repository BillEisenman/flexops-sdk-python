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
    api_key="fxk_live_...",
    workspace_id="ws_abc123",
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

### Live label approval (unreleased SDK changes)

Migration: the optional `CreateLabelRequest` model now uses `carrier_code`,
`service_code`, `origin`, `destination`, and `package`. Raw dictionaries use the
camelCase Gateway names shown below. Pass `idempotency_key` to the method, not
inside the request body. See [CHANGELOG.md](CHANGELOG.md) for model changes.

The example below requires this source revision; the published 1.0.2 packages do
not include the new per-call idempotency argument. Release these SDK changes before
using that argument from a package registry.

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
fees. Sandbox execution bypasses approval; batch, return, and raw carrier routes have
separate contracts. The SDK never automatically confirms a preview.

## Authentication

### API Key (recommended)

```python
client = FlexOps(api_key="fxk_live_...", workspace_id="ws_abc123")
```

### Email / Password

```python
client = FlexOps(base_url="https://gateway.flexops.io")
client.auth.login("user@example.com", "password")
client.workspace_id = "ws_abc123"
```

## Direct Carrier Operations

Access carrier-specific endpoints when you need full control:

```python
# USPS domestic label
label = client.carriers.usps.create_domestic_label({
    "imageType": "PDF",
    "mailClass": "PRIORITY_MAIL",
    "weightInOunces": 16,
    # ... full USPS payload
})

# FedEx rate quote
rates = client.carriers.fedex.get_rates({...})

# UPS tracking
info = client.carriers.ups.track({"trackingNumber": "1Z999AA10123456784"})

# DHL shipment
shipment = client.carriers.dhl.create_shipment({...})
```

## Webhook Verification

```python
from flexops import WebhooksResource

is_valid = WebhooksResource.verify_signature(
    payload=request.body.decode(),
    signature=request.headers["X-FlexOps-Signature"],
    secret="whsec_...",
)
```

## Curl Quickstart

Every SDK method is a thin wrapper around the FlexOps REST API. If you want to verify the API before committing to the SDK — or you're integrating from a language we don't ship a SDK for — these curl invocations hit the same endpoints:

```bash
# Shop rates across all connected carriers
curl -X POST https://gateway.flexops.io/api/shipping/rates \
  -H "X-API-Key: fxk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001", "countryCode": "US"},
    "destination": {"addressLine1": "456 Oak Ave", "city": "Los Angeles", "stateProvince": "CA", "postalCode": "90210", "countryCode": "US"},
    "package": {"weight": 16, "weightUnit": "oz"}
  }'

# Preview a live label; this does not purchase it.
curl -X POST https://gateway.flexops.io/api/workspaces/ws_abc123/shipping/labels \
  -H "X-API-Key: fxk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "carrierCode": "USPS", "serviceCode": "GROUND_ADVANTAGE",
    "origin": {"name": "Warehouse", "addressLine1": "123 Main St", "city": "New York", "stateProvince": "NY", "postalCode": "10001", "countryCode": "US"},
    "destination": {"name": "Customer", "addressLine1": "456 Oak Ave", "city": "Los Angeles", "stateProvince": "CA", "postalCode": "90210", "countryCode": "US"},
    "package": {"weight": 16, "weightUnit": "oz"},
    "maximumPostageAmount": 10.25
  }'

# After explicit approval, resend the same body with confirmationToken from
# the preview and an Idempotency-Key header unique to this purchase.
# See the SDK example above; retain that key for retries.

# Track a shipment
curl https://gateway.flexops.io/api/workspaces/ws_abc123/shipping/track/9400111899223456789012 \
  -H "X-API-Key: fxk_live_..."

# Cancel a label (via the unified carrier-agnostic endpoint)
curl -X DELETE https://gateway.flexops.io/api/v3.0/shipping/Usps/cancel/9400111899223456789012 \
  -H "X-API-Key: fxk_live_..."
```

Use an `fxk_test_...` key instead of `fxk_live_...` to hit the sandbox environment; mock carriers respond, no real charges, no real labels.

## Resources

| Resource | Methods | Description |
|----------|---------|-------------|
| `client.auth` | 10 | Login, register, password management |
| `client.workspaces` | 8 | Workspace CRUD, membership |
| `client.shipping` | 12 | Rate shopping, labels, tracking, batch |
| `client.carriers` | 76 | USPS, UPS, FedEx, DHL direct endpoints |
| `client.webhooks` | 8 | Subscription CRUD, signature verification |
| `client.wallet` | 4 | Balance, transactions, auto-reload |
| `client.insurance` | 5 | Quotes, purchase, claims |
| `client.returns` | 9 | RMA lifecycle management |
| `client.api_keys` | 4 | Key creation, rotation, revocation |
| `client.analytics` | 16 | Shipments, orders, carrier analytics |
| `client.orders` | 12 | Order management |
| `client.inventory` | 5 | Warehouse inventory |
| `client.pickups` | 4 | Carrier pickup scheduling |
| `client.scan_forms` | 3 | USPS scan forms |
| `client.rules` | 6 | Shipping automation rules |

## Configuration

```python
client = FlexOps(
    base_url="https://gateway.flexops.io",  # API base URL
    api_key="fxk_live_...",              # API key auth
    workspace_id="ws_abc123",            # Default workspace
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
