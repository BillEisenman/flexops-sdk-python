# Changelog

All notable changes to the FlexOps Python SDK are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (breaking)
- `webhooks.create(url, events)` and `webhooks.update(id, {"events": [...]})` send the list as the Gateway's comma-separated `eventTypes`; before, the Gateway ignored the `events` field and subscribed to every event. Both raise `ValueError`, without calling the API, for an empty list or a name FlexOps never sends (such as `label.created`). `events` is now optional on `create` (leave it out for every event), and `create` takes a keyword-only `description`. The `WebhookSubscription` model now describes the Gateway response (`event_types` string, `status`, `description`, `consecutive_failures`, `updated_at`, and `secret` only on create; the never-populated `events` and `is_active` are removed), and `CreateWebhookRequest` the Gateway body (`url`, `description`, `event_types`).
- `WebhooksResource.verify_signature(payload, signature, secret)` now requires a keyword-only `timestamp`: `verify_signature(payload, signature, secret, *, timestamp, tolerance=300, now=None)`. Pass the `X-FlexOps-Timestamp` header. Calls without it raise `TypeError`. The old helper never matched a real delivery: it signed the body alone and compared against bare hex, while the Gateway signs `{timestamp}.{raw body}` and sends `sha256=<hex>` (#41).

### Added
- `WebhookEventType` (`str` enum) with the event names FlexOps sends and matches subscriptions on: `LabelCreated`, `LabelCanceled`, `BatchCompleted`, and, for USPS push-tracking pilot workspaces, `TrackingUpdated` and `TrackingDelivered`. The README has a subscription sample and the event table.
- `HazmatClassification` (`IntEnum`, the Gateway numbers) and an optional `hazmat_classification` on `CreateLabelRequest` and `RateRequest`. It is sent only when set; the SDK never defaults it. Labels without an `order_id` must declare it (`HazmatClassification.NONE` for an ordinary parcel).
- `returns.generate_label(return_id, hazmat_classification=...)` sends a declared HAZMAT class with a return label.
- `returns.generate_label` also takes `weight_oz`, `length_in`, `width_in`, `height_in`, `carrier_code`, `service_type` and `payment_confirmed`. The Gateway needs the package: a workspace with no default shipping preset gets a 400 (`PackageMeasurementsRequired`) naming the missing fields when it is left out (Gateway #672).
- `shipping.get_rates`, `get_cheapest_rate` and `get_fastest_rate` accept a `RateRequest` model as well as a dict.
- `BatchLabelItem` and `CreateBatchLabelRequest` mirror the Gateway batch body; `create_batch` and `preview_batch` accept them. `BatchLabelRequest` is deprecated (it never matched the Gateway).

### Fixed
- `WebhooksResource.verify_signature` verifies the Gateway signature: HMAC-SHA256 over `{X-FlexOps-Timestamp}.{raw body}` keyed with the `whsec_...` secret, accepting `sha256=<hex>` or bare hex, compared in constant time. It returns `False` for missing or non-numeric timestamps and timestamps more than `tolerance` seconds (default 300) from now; `now` overrides the clock for tests. `payload` may be the raw body bytes or a string. An empty secret raises `ValueError` (#41).
- README webhook sample: verifies the raw body with the timestamp header and reads the event name from `X-FlexOps-Event`; the body is the event data with no `{"type", "data"}` envelope (#41).
- `returns.generate_label(return_id)` sends `{}`; it sent no body, which the Gateway return-label route refuses with 400.
- `shipping.create_label()` posts to the Gateway route `/api/shipping/labels`; it used a workspace-scoped path the Gateway does not serve.
- `shipping.track`, `cancel_label`, `get_carriers`, `get_recommendations`, `predict_delivery` and `get_savings` use the Gateway `/api/shipping/...` routes instead of workspace-scoped paths the Gateway does not serve. `cancel_label(label_id, carrier_code)` now needs the carrier code the Gateway requires; without it the SDK raises `ValueError` before any request.
- `shipping.validate_address()` posts the Gateway `{"address": {...}}` request to `/api/shipping/addresses/validate`, and maps a legacy `street1`/`state`/`zip` address to the Gateway field names.

## [2.0.0] - 2026-09-19

### Bounded label purchase support

- Single-label requests support maximumPostageAmount and confirmationToken.
- CreateLabel/create_label accepts a per-purchase idempotency key and preserves it on retries.
- Preview and purchase responses are raw objects, not success/data envelopes.
- Gateway errorCode is preserved on SDK errors.
- Read the README approval flow and migration notes before upgrading.
- Request models now use carrierCode/serviceCode/origin/destination/package and existing ShippingAddress/ShippingPackage types. Migrate the former carrier/service/fromAddress/toAddress/parcel fields. BatchLabelRequest also shares this corrected request model; approval fields remain optional.
- Label uses carrierCode and currency; service is not part of the Gateway label response.
- create_label accepts CreateLabelRequest or a raw dictionary; its return value remains a dictionary. LabelPurchasePreview is exported for optional response validation. Pass idempotency_key as a method keyword, not a request-body field.

### Changed
- README: added a curl quickstart section so developers can verify the FlexOps API before committing to the SDK.
- Retargeted repository URL references to `github.com/BillEisenman/flexops-sdk-python` (organization migration from `FlexOps/`).

## [1.0.0] - 2026-03-04

### Added
- Initial public release.
- High-level shipping operations: rate shopping, label creation, tracking, batch labels, cancel.
- API key and email/password authentication.
- Webhook signature verification (HMAC-SHA256) via `WebhooksResource.verify_signature`.
- 15 resource clients covering auth, workspaces, shipping, carriers, webhooks, wallet, insurance, returns, api keys, analytics, orders, inventory, pickups, scan forms, and rules.
- Pydantic v2 models with full type hints; requests for HTTP.
