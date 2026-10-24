# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-10-19
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

import json
import re
import uuid

import pytest
import requests
import responses

from flexops import FlexOps, FlexOpsError
from tests.conftest import BASE_URL

WS_ID = "ws-test-001"
HOOKS = f"{BASE_URL}/api/workspaces/{WS_ID}/webhooks"


@pytest.fixture
def retrying():
    return FlexOps(base_url=BASE_URL, api_key="fxk_test_abc123", workspace_id=WS_ID,
                   retry={"max_retries": 2, "base_delay": 0.001})


def key_of(call: int) -> str | None:
    return responses.calls[call].request.headers.get("Idempotency-Key")


class TestWriteRetries:
    """The Gateway replays a keyed POST/PUT/PATCH, so a write may retry only with the same key."""

    @responses.activate
    def test_sends_one_generated_key_on_every_attempt(self, retrying):
        responses.add(responses.POST, HOOKS, json={"message": "Unavailable"}, status=503)
        responses.add(responses.POST, HOOKS, json={"success": True, "data": {"id": "wh-1"}}, status=201)

        retrying.webhooks.create("https://example.test/hook")

        assert len(responses.calls) == 2
        assert uuid.UUID(key_of(0))
        assert key_of(1) == key_of(0)

    @responses.activate
    def test_resends_the_same_scan_form_request_id_on_every_attempt(self, retrying):
        forms = f"{BASE_URL}/api/workspaces/{WS_ID}/scan-forms"
        responses.add(responses.POST, forms, json={"message": "Unavailable"}, status=503)
        responses.add(responses.POST, forms, json={"success": True, "data": {"scanFormId": "sf-1"}})

        retrying.scan_forms.create(["9400"], manifest_date="2026-09-08")

        ids = [json.loads(call.request.body)["requestId"] for call in responses.calls]
        assert len(ids) == 2
        assert uuid.UUID(ids[0])
        assert ids[1] == ids[0]

    @responses.activate
    def test_resends_the_generated_request_id_when_a_scan_form_model_has_none(self, retrying):
        from flexops import ScanFormRequest

        forms = f"{BASE_URL}/api/workspaces/{WS_ID}/scan-forms"
        responses.add(responses.POST, forms, json={"message": "Unavailable"}, status=503)
        responses.add(responses.POST, forms, json={"success": True, "data": {"scanFormId": "sf-1"}})

        retrying.scan_forms.create(ScanFormRequest(tracking_numbers=["9400"], manifest_date="2026-09-08"))

        ids = [json.loads(call.request.body)["requestId"] for call in responses.calls]
        assert len(ids) == 2
        assert uuid.UUID(ids[0])
        assert ids[1] == ids[0]

    @responses.activate
    def test_generates_a_new_key_for_each_separate_write(self, retrying):
        responses.add(responses.POST, HOOKS, json={"success": True, "data": {"id": "wh-1"}}, status=201)

        retrying.webhooks.create("https://example.test/hook")
        retrying.webhooks.create("https://example.test/hook")

        assert key_of(1) != key_of(0)

    @responses.activate
    def test_put_and_patch_carry_a_key(self, retrying):
        responses.add(responses.PUT, f"{HOOKS}/wh-1", json={"success": True})
        responses.add(responses.PATCH, f"{HOOKS}/wh-1", json={"success": True})

        retrying.webhooks.update("wh-1", {"url": "https://example.test/hook"})
        retrying._http.patch(f"/api/workspaces/{WS_ID}/webhooks/wh-1", {})

        assert uuid.UUID(key_of(0)) and uuid.UUID(key_of(1))

    @responses.activate
    def test_keeps_the_callers_key(self, retrying):
        url = f"{BASE_URL}/api/workspaces/{WS_ID}/insurance/policies"
        responses.add(responses.POST, url, json={"message": "Bad gateway"}, status=502)
        responses.add(responses.POST, url, json={"success": True}, status=201)
        responses.add(responses.POST, f"{BASE_URL}/api/workspaces/{WS_ID}/insurance/quote", json={"success": True})

        retrying.insurance.purchase(tracking_number="1Z", carrier_code="UPS", declared_value=100,
                                    idempotency_key="policy-001")
        retrying._http.post(f"/api/workspaces/{WS_ID}/insurance/quote", {}, headers={"idempotency-key": "k-2"})

        assert [key_of(0), key_of(1)] == ["policy-001", "policy-001"]
        # A caller key in any casing is not doubled with a generated one.
        assert responses.calls[2].request.headers["Idempotency-Key"] == "k-2"

    @responses.activate
    def test_does_not_retry_a_write_after_a_500(self, retrying):
        # The Gateway does not cache a 500, so a retry would run the write (and any charge) again.
        responses.add(responses.POST, HOOKS, json={"message": "Internal error"}, status=500)

        with pytest.raises(FlexOpsError) as error:
            retrying.webhooks.create("https://example.test/hook")

        assert error.value.status == 500
        assert len(responses.calls) == 1

    @responses.activate
    def test_retries_a_dropped_write_with_the_same_key(self, retrying):
        responses.add(responses.POST, HOOKS, body=requests.ConnectionError("connection reset"))
        responses.add(responses.POST, HOOKS, body=requests.Timeout("read timed out"))
        responses.add(responses.POST, HOOKS, json={"success": True, "data": {"id": "wh-1"}}, status=201)

        result = retrying.webhooks.create("https://example.test/hook")

        assert result["data"]["id"] == "wh-1"
        assert len(responses.calls) == 3
        assert key_of(0) == key_of(1) == key_of(2)

    @responses.activate
    def test_waits_out_an_in_flight_duplicate(self, retrying):
        responses.add(responses.POST, HOOKS, json={"success": False, "errorCode": "IDEMPOTENCY_CONFLICT"}, status=409)
        responses.add(responses.POST, HOOKS, json={"success": True, "data": {"id": "wh-1"}}, status=201)

        result = retrying.webhooks.create("https://example.test/hook")

        assert result["data"]["id"] == "wh-1"
        assert len(responses.calls) == 2
        assert key_of(1) == key_of(0)

    @responses.activate
    def test_does_not_retry_a_reused_key_with_a_different_request(self, retrying):
        # Gateway #736: a key reused with a different body is 422 IDEMPOTENCY_KEY_REUSED, never replayed.
        responses.add(responses.POST, HOOKS, json={"success": False, "errorCode": "IDEMPOTENCY_KEY_REUSED",
                                                   "message": "Idempotency key reused"}, status=422)

        with pytest.raises(FlexOpsError) as error:
            retrying.webhooks.create("https://example.test/hook")

        assert (error.value.status, error.value.code) == (422, "IDEMPOTENCY_KEY_REUSED")
        assert len(responses.calls) == 1

    @responses.activate
    def test_does_not_retry_the_pascal_case_idempotency_conflict(self, retrying):
        # Label purchase answers 409 IdempotencyConflict for altered inputs; only the exact uppercase code retries.
        url = f"{BASE_URL}/api/shipping/labels"
        responses.add(responses.POST, url, json={"errorCode": "IdempotencyConflict"}, status=409)

        with pytest.raises(FlexOpsError) as error:
            retrying.shipping.create_label({"maximumPostageAmount": 1}, idempotency_key="label-1")

        assert error.value.code == "IdempotencyConflict"
        assert len(responses.calls) == 1

    @responses.activate
    def test_does_not_retry_any_other_409(self, retrying):
        responses.add(responses.POST, HOOKS, json={"success": False, "errorCode": "CONFLICT"}, status=409)

        with pytest.raises(FlexOpsError) as error:
            retrying.webhooks.create("https://example.test/hook")

        assert error.value.status == 409
        assert len(responses.calls) == 1

    @responses.activate
    def test_retries_a_rate_limited_write(self, retrying):
        responses.add(responses.POST, HOOKS, json={"message": "slow down"}, status=429, headers={"retry-after": "0"})
        responses.add(responses.POST, HOOKS, json={"success": True, "data": {"id": "wh-1"}}, status=201)

        retrying.webhooks.create("https://example.test/hook")

        assert len(responses.calls) == 2
        assert key_of(1) == key_of(0)


class TestDeleteRetries:
    """The idempotency middleware does not cover DELETE, so it is resent only after a 429."""

    @responses.activate
    def test_does_not_resend_a_delete_after_a_dropped_connection(self, retrying):
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", body=requests.ConnectionError("connection reset"))

        with pytest.raises(FlexOpsError) as error:
            retrying.webhooks.delete("wh-1")

        assert error.value.code == "CONNECTION_ERROR"
        assert len(responses.calls) == 1

    @responses.activate
    def test_does_not_resend_a_delete_after_a_timeout(self, retrying):
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", body=requests.Timeout("read timed out"))

        with pytest.raises(FlexOpsError) as error:
            retrying.webhooks.delete("wh-1")

        assert error.value.code == "TIMEOUT"
        assert len(responses.calls) == 1

    @responses.activate
    def test_does_not_resend_a_delete_after_a_503(self, retrying):
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", json={"message": "Unavailable"}, status=503)

        with pytest.raises(FlexOpsError):
            retrying.webhooks.delete("wh-1")

        assert len(responses.calls) == 1
        assert key_of(0) is None

    @responses.activate
    def test_resends_a_delete_after_a_429(self, retrying):
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", json={"message": "slow down"}, status=429)
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", status=204)

        assert retrying.webhooks.delete("wh-1") is None
        assert len(responses.calls) == 2


class TestGetRetries:
    @responses.activate
    def test_get_retries_on_500_and_dropped_connections_without_a_key(self, retrying):
        responses.add(responses.GET, HOOKS, json={"message": "Internal error"}, status=500)
        responses.add(responses.GET, HOOKS, body=requests.ConnectionError("connection reset"))
        responses.add(responses.GET, HOOKS, json={"success": True, "data": []})

        assert retrying.webhooks.list()["success"] is True
        assert len(responses.calls) == 3
        assert key_of(0) is None


class TestEmptyResponses:
    @responses.activate
    def test_204_returns_none(self, client):
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", status=204)

        assert client.webhooks.delete("wh-1") is None

    @responses.activate
    def test_204_labelled_json_is_not_parsed(self, client):
        responses.add(responses.DELETE, f"{HOOKS}/wh-1", body=b"", status=204, content_type="application/json")

        assert client.webhooks.delete("wh-1") is None

    @responses.activate
    def test_empty_200_returns_none(self, client):
        responses.add(responses.POST, re.compile(rf"{HOOKS}/wh-1/test"), body=b"", status=200,
                      headers={"Content-Length": "0"}, content_type="application/json")

        assert client.webhooks.test("wh-1") is None

    @responses.activate
    def test_binary_body_passes_through(self, client):
        url = f"{BASE_URL}/api/workspaces/{WS_ID}/labels/batch/job-1/items/item-1/label"
        responses.add(responses.GET, url, body=b"%PDF-1.7", content_type="application/pdf")

        assert client.shipping.download_batch_label("job-1", "item-1") == b"%PDF-1.7"
