# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

import pytest
import responses

from flexops import FlexOps

BASE_URL = "http://localhost:5000"


@pytest.fixture
def mock_responses():
    """Activate the responses mock for the test."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def client():
    """Create a test client pointing at localhost."""
    return FlexOps(
        base_url=BASE_URL,
        api_key="fxk_test_abc123",
        workspace_id="ws-test-001",
    )


@pytest.fixture
def client_no_key():
    """Create a test client without API key."""
    return FlexOps(
        base_url=BASE_URL,
        workspace_id="ws-test-001",
    )
