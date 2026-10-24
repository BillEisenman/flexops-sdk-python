# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-10-24
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

"""SCAN form replies as the Gateway writes them (ScanFormsController, ScanFormDto), from a fixture."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import responses

from flexops import FlexOps, FlexOpsError, ScanForm, ScanFormState
from tests.conftest import BASE_URL

WS = f"{BASE_URL}/api/workspaces/ws-test-001"
FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "scan-forms.json").read_text(encoding="utf-8"))


@responses.activate
def test_a_created_form_reads_into_scan_form(client):
    responses.add(responses.POST, f"{WS}/scan-forms", json=FIXTURES["created"])

    reply = client.scan_forms.create(["9400111899223456789014", "9400111899223456789021"], manifest_date="2026-09-08")
    form = ScanForm.model_validate(reply["data"])

    assert form.scan_form_id == "3f2b8c1e9d4a4f6b8a7e2c5d1b0f9e88"
    assert form.state == ScanFormState.CREATED
    assert form.success is True
    assert form.is_sandbox is False
    assert form.manifest_number == "9475711899560013735215"
    assert form.manifest_date == datetime(2026, 9, 8)
    assert form.created_at_utc == datetime(2026, 9, 8, 21, 14, 3, 512000, tzinfo=timezone.utc)
    assert form.package_count == 2
    assert form.origin_postal_code == "78701"
    assert form.tracking_numbers == ["9400111899223456789014", "9400111899223456789021"]
    assert form.error_message is None
    assert form.pdf_bytes()[:5] == b"%PDF-"
    # The deprecated names, which the Gateway never sent, now carry the real values.
    assert form.form_data == form.scan_form_image
    assert form.created_at == "2026-09-08T21:14:03.512Z"


@responses.activate
def test_listed_forms_include_sandbox_forms_without_a_pdf_and_unresolved_operations(client):
    responses.add(responses.GET, f"{WS}/scan-forms", json=FIXTURES["list"])

    forms = [ScanForm.model_validate(item) for item in client.scan_forms.list()["data"]]

    assert len(forms) == 2
    sandbox, unknown = forms
    assert sandbox.is_sandbox and sandbox.scan_form_image is None and sandbox.pdf_bytes() is None
    assert sandbox.manifest_number.startswith("SBOX")
    assert sandbox.form_data is None
    assert unknown.state == ScanFormState.OUTCOME_UNKNOWN
    assert unknown.success is False
    assert unknown.manifest_number == ""
    assert unknown.package_count == 2


@responses.activate
def test_get_reads_one_form(client):
    responses.add(responses.GET, f"{WS}/scan-forms/3f2b8c1e9d4a4f6b8a7e2c5d1b0f9e88", json=FIXTURES["created"])

    form = ScanForm.model_validate(client.scan_forms.get("3f2b8c1e9d4a4f6b8a7e2c5d1b0f9e88")["data"])

    assert form.scan_form_id == "3f2b8c1e9d4a4f6b8a7e2c5d1b0f9e88"


@pytest.mark.parametrize("name", ["requestIdReused", "needsReview"])
@responses.activate
def test_a_gateway_409_raises_once_without_a_retry(name):
    reply = FIXTURES[name]
    responses.add(responses.POST, f"{WS}/scan-forms", json=reply["body"], status=reply["status"])
    client = FlexOps(base_url=BASE_URL, api_key="fxk_test_abc123", workspace_id="ws-test-001",
                     retry={"max_retries": 2, "base_delay": 0.001})

    with pytest.raises(FlexOpsError) as raised:
        client.scan_forms.create(["9400"], manifest_date="2026-09-08", request_id="req-1")

    assert raised.value.status == 409
    assert str(raised.value) == reply["body"]["message"]
    assert len(responses.calls) == 1
