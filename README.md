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
    "fromZip": "10001",
    "toZip": "90210",
    "weight": 16,
    "weightUnit": "oz",
})

# Create a label with the cheapest rate
label = client.shipping.create_label({
    "carrier": rates["data"][0]["carrier"],
    "service": rates["data"][0]["service"],
    "fromAddress": {
        "name": "Warehouse",
        "street1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "country": "US",
    },
    "toAddress": {
        "name": "Customer",
        "street1": "456 Oak Ave",
        "city": "Los Angeles",
        "state": "CA",
        "zip": "90210",
        "country": "US",
    },
    "parcel": {"weight": 16, "weightUnit": "oz"},
})

# Track a shipment
tracking = client.shipping.track("9400111899223456789012")
```

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
curl -X POST https://gateway.flexops.io/api/workspaces/ws_abc123/shipping/rates \
  -H "X-API-Key: fxk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "fromAddress": {"street1": "123 Main St", "city": "New York", "state": "NY", "zip": "10001", "country": "US"},
    "toAddress":   {"street1": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zip": "90210", "country": "US"},
    "parcel":      {"weight": 16, "weightUnit": "oz"}
  }'

# Create a label
curl -X POST https://gateway.flexops.io/api/workspaces/ws_abc123/shipping/labels \
  -H "X-API-Key: fxk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "carrier":  "USPS",
    "service":  "PRIORITY_MAIL",
    "fromAddress": {"name": "Warehouse", "street1": "123 Main St", "city": "New York", "state": "NY", "zip": "10001", "country": "US"},
    "toAddress":   {"name": "Customer",  "street1": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zip": "90210", "country": "US"},
    "parcel":   {"weight": 16, "weightUnit": "oz"}
  }'

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

Proprietary - FlexOps, LLC
