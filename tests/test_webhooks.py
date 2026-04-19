# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

import hashlib
import hmac

import responses

from flexops import WebhooksResource
from tests.conftest import BASE_URL

WS_ID = "ws-test-001"


class TestWebhookSignatureVerification:
    def test_verifies_valid_signature(self):
        secret = "whsec_test123"
        payload = '{"event":"label.created","data":{}}'
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        assert WebhooksResource.verify_signature(payload, signature, secret) is True

    def test_rejects_invalid_signature(self):
        assert WebhooksResource.verify_signature("payload", "0" * 64, "secret") is False


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
