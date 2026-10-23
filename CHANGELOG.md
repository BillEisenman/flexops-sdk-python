# Changelog

All notable changes to the FlexOps Python SDK are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-10-22

3.1.0 adds multi-package labels and RMA reads, and corrects the returns `get` docs. Existing code keeps working.

### Added
- `shipping.create_multi_package(request, *, idempotency_key=None)` buys labels for one order shipped in 1 to 99
  boxes (`POST /api/shipping/multi-package`). Typed with `MultiPackageShipmentRequest` and `MultiPackageDetail`;
  `MultiPackageShipmentResponse` and `MultiPackageLabelResult` describe the reply. The request model accepts only
  `HazmatClassification.NONE` (or nothing) for `hazmat_classification`, the one class the Gateway takes on this
  route (anything else is 400 `HazmatNotSupported`).
- `returns.get_rma(rma_number)` and `returns.list_rmas()` read return authorizations (`GET .../returns/rma/{rmaNumber}`
  and `GET .../returns/rma`). There was no way to read an RMA back after creating it.
- `FlexOpsError.data` carries the envelope's `data` on an error reply. A multi-package 422 `AllPackagesFailed` or
  409 `OutcomeUnknown` puts the per-box results there.

### Fixed
- `returns.get()` takes the numeric return ID (`int | str`) and says so. It was documented as reading a return
  authorization, but the Gateway route reads a received return by return ID; an RMA number matched no route.
  Use `get_rma()` for an RMA. `returns.list()` is documented as listing received returns.

## [3.0.1] - 2026-10-22

### Fixed
- `webhooks.delete()` and `rules.delete()` are annotated `-> None`. The Gateway answers both with 204 No Content,
  so they always returned `None`, but were annotated as a response dict, so type checkers accepted code such as
  `client.webhooks.delete(id)["success"]`, which raises `TypeError`.

## [3.0.0] - 2026-10-19

The SDK now covers only the documented public Gateway API. Portal features and calls with no
Gateway route are removed; the calls that remain send the routes, bodies and enum numbers the Gateway
expects; the legacy carrier proxy writes are deprecated; and retries can no longer repeat a purchase.

### Removed (breaking)
- `client.api_keys` (`ApiKeysResource`, `ApiKeyInfo`, `CreateApiKeyRequest`, `CreateApiKeyResponse`): API keys are managed in the portals.
- `client.offsets`: its per-label routes never existed on the Gateway. Use `client.carbon_offsets`.
- `wallet.add_funds`, `wallet.list_transactions` and `wallet.configure_auto_reload`: wallet funding is managed in the portals.
- `auth.register`, `get_profile`, `update_profile`, `change_password`, `forgot_password`, `reset_password` and `verify_email` (and `RegisterRequest`). `login`, `refresh_token` and `logout` remain.
- `workspaces.create` and `workspaces.update` (and `CreateWorkspaceRequest`). `list`, `get` and the member calls remain.
- `returns.approve`, `reject`, `cancel` and `process_refund`: return decisions are made in the portals.
- `webhooks.get(id)`: the Gateway has no such route. Use `webhooks.list()`.
- `orders.create`, `orders.cancel`, `inventory.post_asn_receipt` and `inventory.update_inventory`: writes through the legacy `/api/ApiProxy`, which refuses API-key writes. The proxy reads remain.
- The legacy proxy's label-generation calls, which the Gateway closes (410 Gone in every environment): `carriers.usps.create_domestic_label`, `create_return_label` and `create_international_label`, `carriers.ups.create_label`, `carriers.fedex.create_shipment` and `create_return_shipment`, and `carriers.dhl.create_shipment`. Use `shipping.create_label` and `returns.generate_label`.
- `carriers.dhl.update_pickup`: a `PATCH`, which the proxy does not route.

### Changed (breaking)
- Retries are safe for writes. Every `POST`, `PUT` and `PATCH` sends an `Idempotency-Key`: the caller's, else a UUID generated for the call and reused on each of its retries. Writes retry only on a dropped connection, a timeout, 429, 502, 503, 504 and 409 `IDEMPOTENCY_CONFLICT`, never on 500 (the Gateway does not replay a 500, so a retry could charge twice). `DELETE` retries only on 429. `GET` retries as before. A key reused with a different request gets 422 `IDEMPOTENCY_KEY_REUSED` and is not retried.
- `client.recurring_shipments`, `client.report_schedules` (renamed from `client.reports`) and `client.email_templates` call the Gateway routes; the 2.x paths and shapes never worked. Reads work with any API key or a user token; writes need a user token or an API key granted `recurring-shipments:write`, `report-schedules:write` or `email-templates:write` (otherwise 403 `API_KEY_SCOPE_REQUIRED`).
  - `recurring_shipments`: `list`, `get`, `create`, `update`, `delete`, `pause`, `resume` and `trigger` (with `idempotency_key`; it creates an order) on `recurring-shipments`. Responses are bare JSON; `delete`, `pause`, `resume` and `trigger` return `None` (204).
  - `report_schedules`: `list`, `get`, `create`, `update`, `delete` and `toggle` on `report-schedules`. Responses use the envelope, except `delete` (204, `None`).
  - `email_templates`: `list`, `get`, `upsert` (one `PUT` per `eventType`; there is no separate create or update), `delete` and `preview(subject_template=, html_body_template=)` on `email-templates` (2.x used `shipment-email-templates`). Responses are bare JSON.
  - New `RecurrenceInterval`, `ReportFormat`, `ReportFrequency` and `TrackingEmailEvent` (`IntEnum`, the Gateway numbers).
- The carrier writes through the legacy `/api/ApiProxy` are deprecated: each call raises a `DeprecationWarning` and its docstring says so. They need a user token (`auth.login`), since API keys get 403 `API_KEY_SCOPE_REQUIRED`, and stop working when the proxy is retired on 2027-06-30. Use `client.shipping`, `client.pickups` and `client.scan_forms` where they cover the call. Like any write they now send an `Idempotency-Key` and follow the write retry policy. Carrier reads (`GET`) are unchanged.
- A 2xx response with no body (204, or `Content-Length: 0`) returns `None` instead of `b""`.
- `shipping.validate_address` posts the flat Gateway `AddressValidationRequest` (`name`, `line1`, `line2`, `city`, `state`, `postalCode`, `country`) to the documented `/api/addresses/validate` (scope `shipping:read`), with `X-Workspace-Id` when a workspace is configured. It used the hidden `/api/shipping/addresses/validate` with an `{"address": {...}}` body. `ShippingAddress` and legacy `street1`/`state`/`zip` addresses are still accepted and mapped. `AddressValidationResult` now describes the Gateway result (`is_valid`, `suggested_address`, `is_residential`, `warnings`, `validated_by`, `validation_unavailable`, `checked_at`).
- `wallet.get_balance()` calls `GET /api/wallet/my-balance` with `X-Workspace-Id` and returns the bare `{"hasWallet", "balanceCents", "balance"}`; `WalletBalance` has those fields.
- `hs_codes` calls the Gateway `/api/shipping/hs-codes/search`, `/api/shipping/hs-codes/{code}` and `/api/shipping/landed-cost` with no workspace in the path. They return bare JSON (a list from `search`).
- `insurance.get_quote(carrier_code=, declared_value=, tracking_number=, provider=)` sends `carrierCode` (was `carrier`). `insurance.purchase(tracking_number=, carrier_code=, declared_value=, coverage_tier=, provider=, idempotency_key=)` posts to `insurance/policies` (was the nonexistent `insurance/purchase`). `insurance.file_claim(policy_id, claim_reason=, claim_amount=, evidence_json=)` posts `{policyId, claimReason, claimAmount, evidenceJson}` to `insurance/claims`. `InsuranceQuote` and `InsurancePolicy` now describe the Gateway DTOs.
- `returns.create(order_id=, reason=, items=, order_number=, notes=, customer_email=, reason_id=)` posts to `returns/rma` with a numeric `orderId` and returns the envelope (201). `ReturnRequest.order_id` is an `int`.
- `returns.generate_label(rma_number, ...)` names its first argument for what the route takes, an RMA number, and adds `rate_indicator`. `carrier_code` stays optional (the Gateway defaults it to `usps`).
- `returns.mark_received(rma_id, rma_number=, warehouse_id=, inspected_items=)` sends the Gateway `{rmaNumber, warehouseId, inspectedItems}`; each inspected item is `{partNumber, quantity, disposition (0 restock, 1 dispose, 2 forward), partDescription?, inspectionNotes?}`.
- `rules.reorder(rules)` posts `{"rules": [{"ruleId", "priority"}]}` to `shipping-rules/reorder` (it sent `PUT {"ruleIds"}`). A list of rule IDs is still accepted and given priorities in order. `ShippingRule` has `is_enabled` (was `is_active`) and `warehouse_id`.
- `pickups.list()` reads `pickups/scheduled` (the Gateway has no `GET pickups`); `pickups.get` and `pickups.cancel` take an optional keyword `carrier_code` (the Gateway defaults to `usps`). `PickupRequest` describes the Gateway `SchedulePickupRequest` (`carrier_code`, `pickup_date`, `street`, `city`, `state`, `postal_code`, `package_count`, ...).
- `workspaces.invite_member(email, role)` and `update_member_role(user_id, role)` send the role as the Gateway number (`{"email", "role"}` and `{"newRole"}`); they sent the name, which the Gateway does not bind. `role` takes a `WorkspaceRole`, a name (`"Owner"`, `"Admin"`, `"Member"`, `"Merchant"`) or a number. `Guest` is no longer a role.
- `auth.login` uses the access token the Gateway returns in `data["token"]`; it looked for `data["accessToken"]`, which the Gateway never sends, so the client stayed unauthenticated. `LoginResponse` now describes the Gateway response (`token`, `refresh_token`, `expires_at`, `user_id`, `email`, `first_name`, `last_name`, `roles`, `requires_two_factor`, ...).
- `auth.refresh_token(refresh_token, access_token=None)` posts the Gateway body `{"token", "refreshToken"}`; it sent the refresh token in an `X-Current-Session-Token` header, which the Gateway ignores. `access_token` defaults to the client's current token; with neither, it raises `ValueError` before any request. The new access token replaces the client's.
- `returns.list(page=, page_size=, start_date=, end_date=)` filters by date range, as the Gateway does; the `status` filter, which the Gateway ignored, is removed.
- `Workspace`, `WorkspaceMember` and the new `WorkspaceSummary` and `WorkspaceMemberList` describe the Gateway responses: `list_members()` returns `{"members": [...], "pendingInvites": [...], ...}`, not a list, and roles and statuses are numbers.
- `webhooks.create()` always returns the envelope `{"success": True, "data": <subscription>}`, the shape every other method returns, so `result["data"]["secret"]` is the signing secret. The Gateway answers create with `201` and the bare subscription, not the `{"success", "data"}` envelope its other webhook routes use, so `result["data"]` used to raise `KeyError` and the secret could only be found at `result["secret"]`. A bare body is now wrapped and an envelope passes through unchanged. Code that read `result["id"]` or `result["secret"]` must read `result["data"][...]`.
- `webhooks.create(url, events)` and `webhooks.update(id, {"events": [...]})` send the list as the Gateway's comma-separated `eventTypes`; before, the Gateway ignored the `events` field and subscribed to every event. Both raise `ValueError`, without calling the API, for an empty list or a name FlexOps never sends (such as `label.created`). `events` is now optional on `create` (leave it out for every event), and `create` takes a keyword-only `description`. The `WebhookSubscription` model now describes the Gateway response (`event_types` string, `status`, `description`, `consecutive_failures`, `updated_at`, and `secret` only on create; the never-populated `events` and `is_active` are removed), and `CreateWebhookRequest` the Gateway body (`url`, `description`, `event_types`).
- `WebhooksResource.verify_signature(payload, signature, secret)` now requires a keyword-only `timestamp`: `verify_signature(payload, signature, secret, *, timestamp, tolerance=300, now=None)`. Pass the `X-FlexOps-Timestamp` header. Calls without it raise `TypeError`. The old helper never matched a real delivery: it signed the body alone and compared against bare hex, while the Gateway signs `{timestamp}.{raw body}` and sends `sha256=<hex>` (#41).

### Added
- `client.carbon_offsets` (`CarbonOffsetsResource`): `quote`, `purchase` (with `idempotency_key`), `list`, `get`, `get_summary`, `get_settings` and `update_settings`.
- `rules.test(request)` dry-runs the workspace's shipping rules against a sample shipment.
- `webhooks.test(webhook_id)` sends a test event.
- `WorkspaceRole` (`IntEnum`: `OWNER` 0, `ADMIN` 1, `MEMBER` 2, `MERCHANT` 3) and `SuggestedAddress`.
- A contract test that calls every public method and checks each request against the operations in the Developer Docs OpenAPI snapshot.
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
- `shipping.validate_address()` maps a legacy `street1`/`state`/`zip` address to the Gateway field names.
- README: the curl label cancellation uses `DELETE /api/shipping/labels/{labelId}?carrierCode=USPS`.

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
