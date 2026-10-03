## International USPS labels (gated; not released)

International access requires the server master switch, USPS readiness flag, Enterprise
eligibility and a reviewed destination allowlist. Installing this SDK does not enable it.
The server master also requires a current bounded activation expiry (EnabledUntilUtc);
an expired window refuses new international work even if Enabled remains true.
When disabled, preserve the server's FeatureDisabled refusal; do not retry with another route.

Use the existing normalized shipping rate and label methods. Node/.NET callers use
prepareLabel/PrepareLabelAsync, inspect the preview, then explicitly call
purchaseLabel/PurchaseLabelAsync. Python/Go/PHP/Ruby callers use create_label/CreateLabel/
createLabel twice: first without confirmationToken for a preview, then with the returned
token and the same unchanged shipment, maximum, and stable Idempotency-Key.

`examples/international-label.json` is a serialization fixture, not a runnable purchase.
Replace the fictitious order, addresses, date, and user-supplied AES information with
authorized inputs. Preview does not buy. Never automatically confirm, create a fresh key
after an uncertain result, or retry OutcomeUnknown as a new operation.

Initial scope: existing order, single variable parcel, US origin, USD, PDF,
PRIORITY_INTERNATIONAL (SP) or PRIORITY_EXPRESS_INTERNATIONAL (PA), explicit shipDate
(today through seven days), RETURN or ABANDON. Customs item value and weightOz are
**per unit**; declaredValue is the sum of quantity times value. Top-level declaredValue,
if supplied, must equal customsDeclaration.declaredValue. Optional insurance, signature,
HAZMAT, Hold For Pickup, flat-rate packaging, stateless and batch international are refused.

Retain the approved shipment snapshot, token and idempotency key securely. Tokens contain
private shipment information. Changed customs, date, addresses, service or maximum require
a new preview. Reprints and cancellation are also blocked when international is disabled.
Carrier acceptance, publication and production enablement remain separate release gates.
