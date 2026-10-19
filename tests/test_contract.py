# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-10-19
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

"""Every public SDK method must call an operation the Gateway documents.

The fixture ``fixtures/gateway-operations.json`` lists ``"METHOD /path"`` for each operation in the
Developer Docs OpenAPI snapshot (``Docs/FlexOpsDeveloperDocs/static/openapi/gateway.json``); refresh
it by regenerating that list from the current snapshot when the documented API changes.
"""

from __future__ import annotations

import inspect
import json
import re
import warnings
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import pytest
import responses

from flexops import FlexOps
from flexops.resources import CarriersResource
from tests.conftest import BASE_URL

_FIXTURE = Path(__file__).parent / "fixtures" / "gateway-operations.json"
_PROXY_PREFIX = "/api/apiproxy/"
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Public methods that make no HTTP call.
_NOT_HTTP = {"webhooks.verify_signature"}

# The only methods allowed to send a non-GET through /api/ApiProxy: the deprecated carrier writes,
# which need a user token (the Gateway refuses API-key writes there).
_DEPRECATED_PROXY_WRITES = {
    *(f"carriers.usps.{m}" for m in (
        "get_domestic_rates", "get_domestic_products", "get_domestic_prices", "get_international_rates",
        "get_international_prices", "cancel_domestic_label", "cancel_international_label", "create_pickup",
        "cancel_pickup", "create_scan_form")),
    *(f"carriers.ups.{m}" for m in (
        "validate_address", "get_rates", "create_pickup", "cancel_pickup", "get_transit_times", "get_landed_cost",
        "search_locations", "upload_document", "create_freight_shipment", "get_freight_rate")),
    *(f"carriers.fedex.{m}" for m in (
        "validate_address", "validate_postal_code", "get_rates", "cancel_shipment", "validate_shipment", "track",
        "track_multi_piece", "register_tracking_notification", "create_pickup", "cancel_pickup", "search_locations",
        "get_service_standards", "get_freight_rate", "create_freight_shipment", "ground_close",
        "upload_trade_documents", "create_open_shipment", "add_packages_to_open_shipment", "confirm_open_shipment")),
    *(f"carriers.dhl.{m}" for m in (
        "get_multi_piece_rates", "create_pickup", "cancel_pickup", "calculate_landed_cost", "screen_shipment",
        "upload_invoice")),
}

# Label-generation suffixes the Gateway closes on the proxy (410 Gone in every environment).
_CLOSED_LABEL_SUFFIXES = tuple(s.lower() for s in (
    "generateNewUpsShipLabel", "postNewShipLabelOrder", "postUspsGenerateDomesticShippingLabel",
    "postUspsGenerateDomesticReturnsShippingLabel", "postUspsGenerateInternationalShippingLabel",
    "postUspsGenerateDomesticIndiciaLabel", "postFedExCreateNewShipment", "postFedExCreateNewReturnShipment",
    "postDhlCreateShipment", "postOnTracCreateShipment", "postLsoCreateShipment", "postAusPostCreateShipment",
    "postCanadaPostCreateShipment", "postRoyalMailCreateShipment",
))

# Arguments for methods whose required parameters a generic dummy does not satisfy.
_ARGS: dict[str, tuple[tuple[Any, ...], dict[str, Any]]] = {
    "auth.refresh_token": (("refresh-1", "access-1"), {}),
    "shipping.cancel_label": (("lbl-1", "USPS"), {}),
    "webhooks.create": (("https://example.test/hook", ["LabelCreated"]), {}),
}


def _documented() -> list[tuple[str, re.Pattern[str]]]:
    operations = json.loads(_FIXTURE.read_text(encoding="utf-8"))["operations"]
    documented = []
    for operation in operations:
        method, path = operation.split(" ", 1)
        segments = [re.sub(r"\\\{[^/]*?\\\}", "[^/]+", re.escape(s)) for s in _normalize(path).split("/")]
        documented.append((method, re.compile("/".join(segments))))
    return documented


def _normalize(path: str) -> str:
    """Drops the query and the ``/api/v1`` version prefix; routes are case-insensitive."""
    path = unquote(urlsplit(path).path).lower()
    return "/api" + path[len("/api/v1"):] if path.startswith("/api/v1/") else path


def _dummy(name: str, annotation: Any) -> Any:
    text = str(annotation)
    for prefix, value in (("dict", {}), ("list", ["x-1"]), ("int", 1), ("float", 1.5), ("bool", True),
                          ("str", "x-1"), ("WorkspaceRole", 1), ("Any", {})):
        if text.startswith(prefix):
            return value
    raise AssertionError(f"No dummy for parameter {name}: {text}; add the method to _ARGS")


def _public_methods(client: FlexOps) -> list[tuple[str, Any]]:
    """Every public method of every resource on the client, carrier sub-resources included."""
    targets: list[tuple[str, Any]] = []
    for name, resource in vars(client).items():
        if name.startswith("_"):
            continue
        if isinstance(resource, CarriersResource):
            targets.extend((f"{name}.{carrier}", sub) for carrier, sub in vars(resource).items())
        else:
            targets.append((name, resource))
    methods = []
    for prefix, obj in targets:
        for attr, member in inspect.getmembers(type(obj), callable):
            if not attr.startswith("_"):
                methods.append((f"{prefix}.{attr}", getattr(obj, attr)))
    return methods


def _call(qualified: str, method: Any) -> None:
    if qualified in _ARGS:
        args, kwargs = _ARGS[qualified]
        method(*args, **kwargs)
        return
    args, kwargs = [], {}
    for param in inspect.signature(method).parameters.values():
        if param.default is not inspect.Parameter.empty or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        value = _dummy(param.name, param.annotation)
        if param.kind is param.KEYWORD_ONLY:
            kwargs[param.name] = value
        else:
            args.append(value)
    method(*args, **kwargs)


@pytest.fixture
def recorded_calls() -> list[tuple[str, str, str]]:
    """Calls every public method through the ``responses`` fake and records (method name, verb, path)."""
    client = FlexOps(base_url=BASE_URL, api_key="fxk_test_abc123", workspace_id="ws-test-001",
                     retry={"max_retries": 0})
    calls: list[tuple[str, str, str]] = []
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        for verb in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            rsps.add(verb, re.compile(re.escape(BASE_URL) + r"/.*"), json={})
        for qualified, method in _public_methods(client):
            if qualified in _NOT_HTTP:
                continue
            before = len(rsps.calls)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _call(qualified, method)
            deprecated = any(issubclass(w.category, DeprecationWarning) for w in caught)
            assert deprecated == (qualified in _DEPRECATED_PROXY_WRITES), f"{qualified} deprecation warning"
            made = rsps.calls[before:]
            assert len(made) == 1, f"{qualified} made {len(made)} requests"
            calls.append((qualified, made[0].request.method, made[0].request.url))
    return calls


def test_every_public_method_calls_a_documented_operation(recorded_calls):
    documented = _documented()

    def is_documented(verb: str, path: str) -> bool:
        # /api/ApiProxy/{path} is the legacy proxy's catch-all: any depth, for the verbs it documents.
        if path.startswith(_PROXY_PREFIX):
            path = _PROXY_PREFIX + "x"
        return any(verb == method and pattern.fullmatch(path) for method, pattern in documented)

    undocumented = [f"{name}: {verb} {_normalize(url)}" for name, verb, url in recorded_calls
                    if not is_documented(verb, _normalize(url))]
    assert undocumented == []


def test_only_deprecated_methods_write_through_the_legacy_proxy(recorded_calls):
    # The Gateway refuses API-key writes through /api/ApiProxy; the deprecated carrier writes need a user token.
    proxy_writes = {name for name, verb, url in recorded_calls
                    if verb in _WRITE_METHODS and _normalize(url).startswith(_PROXY_PREFIX)}
    assert proxy_writes == _DEPRECATED_PROXY_WRITES


def test_proxy_writes_are_marked_deprecated():
    client = FlexOps(base_url=BASE_URL, workspace_id="ws-test-001")
    methods = dict(_public_methods(client))
    assert all(getattr(methods[name], "__deprecated__", None) for name in _DEPRECATED_PROXY_WRITES)
    assert all("deprecated" in methods[name].__doc__ for name in _DEPRECATED_PROXY_WRITES)


def test_no_proxy_call_uses_a_closed_label_route_or_patch(recorded_calls):
    proxy = [(name, verb, _normalize(url)) for name, verb, url in recorded_calls
             if _normalize(url).startswith(_PROXY_PREFIX)]
    assert [name for name, _, path in proxy if path.endswith(_CLOSED_LABEL_SUFFIXES)] == []
    assert [name for name, verb, _ in proxy if verb == "PATCH"] == []


def test_every_public_method_is_exercised(recorded_calls):
    client = FlexOps(base_url=BASE_URL, workspace_id="ws-test-001")
    public = {name for name, _ in _public_methods(client)} - _NOT_HTTP
    assert {name for name, _, _ in recorded_calls} == public
    assert len(recorded_calls) == len(public) > 90


def test_the_matcher_rejects_an_undocumented_route():
    documented = _documented()

    def matches(verb: str, url: str) -> bool:
        return any(verb == m and p.fullmatch(_normalize(url)) for m, p in documented)

    assert matches("GET", f"{BASE_URL}/api/v1/Workspaces/ws-1/members")
    assert matches("DELETE", f"{BASE_URL}/api/shipping/labels/lbl-1?carrierCode=USPS")
    assert not matches("POST", f"{BASE_URL}/api/shipping/addresses/validate")
    assert not matches("GET", f"{BASE_URL}/api/workspaces/ws-1/pickups")
    assert not matches("GET", f"{BASE_URL}/api/workspaces/ws-1/members/extra/segment")
