# Changelog

All notable changes to the FlexOps Python SDK are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Bounded label purchase support

- Single-label requests support maximumPostageAmount and confirmationToken.
- CreateLabel/create_label accepts a per-purchase idempotency key and preserves it on retries.
- Preview and purchase responses are raw objects, not success/data envelopes.
- Gateway errorCode is preserved on SDK errors.
- No package has been published by this change. Read the README approval flow before migrating.
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
