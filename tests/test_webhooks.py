# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

import pytest
import responses

from flexops import WebhooksResource
from tests.conftest import BASE_URL

WS_ID = "ws-test-001"

# Fixed vector made with the Gateway algorithm (WebhookDeliveryService): lowercase hex HMAC-SHA256
# over the UTF-8 string "{timestamp}.{raw body}", keyed with the UTF-8 bytes of the whole
# "whsec_..." secret. Computed once with the standard library hmac module and cross-checked with
# `openssl dgst -sha256 -hmac`; hard-coded so the test does not reuse the code under test.
SECRET = "whsec_AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
TIMESTAMP = "1760000000"
BODY = '{"labelId":"lbl_123","trackingNumber":"9400100000000000000000","carrierCode":"USPS"}'
SIGNATURE = "sha256=02a9afec40dedbbd4e698f0ff995ba9f267651f836f94e571d7f6f28f6b8d1e9"
# What the old helper produced: HMAC of the body alone. A real delivery never carries it.
BODY_ONLY_HEX = "7eaa376c69823a5a584fa676486bee36ed90dba3f13090b1fcfe5500c611689a"
NOW = int(TIMESTAMP)


def verify(payload=BODY, signature=SIGNATURE, secret=SECRET, **kwargs):
    kwargs.setdefault("timestamp", TIMESTAMP)
    kwargs.setdefault("now", NOW)
    return WebhooksResource.verify_signature(payload, signature, secret, **kwargs)


class TestWebhookSignatureVerification:
    def test_accepts_server_signed_delivery(self):
        assert verify() is True

    def test_accepts_raw_body_bytes(self):
        assert verify(BODY.encode("utf-8")) is True

    def test_accepts_signature_without_prefix(self):
        assert verify(signature=SIGNATURE.removeprefix("sha256=")) is True

    def test_rejects_other_scheme_prefix(self):
        assert verify(signature=SIGNATURE.replace("sha256=", "sha1=")) is False

    def test_rejects_wrong_secret(self):
        assert verify(secret="whsec_not-the-secret") is False

    def test_rejects_tampered_body(self):
        assert verify(BODY.replace("lbl_123", "lbl_124")) is False

    def test_rejects_timestamp_that_was_not_signed(self):
        assert verify(timestamp="1760000001") is False

    def test_rejects_old_body_only_signature(self):
        assert verify(signature=f"sha256={BODY_ONLY_HEX}") is False
        assert verify(signature=BODY_ONLY_HEX) is False

    def test_accepts_timestamp_at_default_tolerance(self):
        assert verify(now=NOW + 300) is True
        assert verify(now=NOW - 300) is True

    def test_rejects_stale_timestamp(self):
        assert verify(now=NOW + 301) is False

    def test_rejects_future_timestamp_beyond_tolerance(self):
        assert verify(now=NOW - 301) is False

    def test_honours_custom_tolerance(self):
        assert verify(now=NOW + 30, tolerance=10) is False
        assert verify(now=NOW + 3600, tolerance=7200) is True

    @pytest.mark.parametrize(
        "timestamp", [None, "", " ", "abc", "-1760000000", "1.76e9", "1760000000.0", "0x68e0b800", "١٧"]
    )
    def test_rejects_missing_or_non_numeric_timestamp(self, timestamp):
        assert verify(timestamp=timestamp) is False

    @pytest.mark.parametrize(
        "signature",
        [
            None,
            "",
            "sha256=",
            SIGNATURE[:-2],
            SIGNATURE + "00",
            "sha256=" + "z" * 64,
            "sha256=" + "é" * 64,
        ],
        ids=["missing", "empty", "prefix-only", "short", "long", "non-hex", "non-ascii"],
    )
    def test_rejects_malformed_signature_without_raising(self, signature):
        assert verify(signature=signature) is False

    def test_timestamp_is_required(self):
        with pytest.raises(TypeError):
            WebhooksResource.verify_signature(BODY, SIGNATURE, SECRET)

    def test_empty_secret_raises(self):
        with pytest.raises(ValueError):
            verify(secret="")

    def test_checks_real_clock_by_default(self):
        assert WebhooksResource.verify_signature(BODY, SIGNATURE, SECRET, timestamp=TIMESTAMP) is False


class TestWebhookCrud:
    @responses.activate
    def test_create_webhook(self, client):
        responses.add(
            responses.POST,
            f"{BASE_URL}/api/workspaces/{WS_ID}/webhooks",
            json={"success": True, "data": {"id": "wh-001", "url": "https://example.com/hook"}},
            status=200,
        )

        result = client.webhooks.create("https://example.com/hook", ["label.created"])

        assert result["data"]["id"] == "wh-001"

    @responses.activate
    def test_list_webhooks(self, client):
        responses.add(
            responses.GET,
            f"{BASE_URL}/api/workspaces/{WS_ID}/webhooks",
            json={"success": True, "data": []},
            status=200,
        )

        result = client.webhooks.list()
        assert result["success"] is True
