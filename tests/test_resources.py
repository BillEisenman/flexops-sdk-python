# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-10-19
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

"""Routes, bodies and headers checked against the Gateway controllers and DTOs."""

import json
from typing import get_type_hints

import pytest
import responses

from flexops.resources.rules import RulesResource
from flexops.resources.webhooks import WebhooksResource
from tests.conftest import BASE_URL

WS_ID = "ws-test-001"
WS = f"{BASE_URL}/api/workspaces/{WS_ID}"


def sent(call: int = 0):
    return json.loads(responses.calls[call].request.body)


class TestWallet:
    @responses.activate
    def test_get_balance_reads_my_balance_for_the_configured_workspace(self, client):
        responses.add(responses.GET, f"{BASE_URL}/api/wallet/my-balance",
                      json={"hasWallet": True, "balanceCents": 1250, "balance": 12.5})

        result = client.wallet.get_balance()

        assert result == {"hasWallet": True, "balanceCents": 1250, "balance": 12.5}
        assert responses.calls[0].request.headers["X-Workspace-Id"] == WS_ID

    def test_portal_only_wallet_calls_are_gone(self, client):
        for name in ("add_funds", "list_transactions", "configure_auto_reload"):
            assert not hasattr(client.wallet, name), name


class TestHsCodes:
    @responses.activate
    def test_routes_are_not_workspace_scoped(self, client):
        responses.add(responses.GET, f"{BASE_URL}/api/shipping/hs-codes/search", json=[{"code": "6109.10"}],
                      match=[responses.matchers.query_param_matcher(
                          {"query": "t-shirt", "maxResults": "5", "destinationCountry": "CA"})])
        responses.add(responses.GET, f"{BASE_URL}/api/shipping/hs-codes/6109.10", json={"code": "6109.10"})
        responses.add(responses.POST, f"{BASE_URL}/api/shipping/landed-cost", json={"totalLandedCost": 12.0})
        request = {"destinationCountry": "CA", "shippingCost": 9.5, "items": [
            {"description": "T-shirt", "quantity": 2, "value": 10, "weightOz": 6, "originCountry": "US"}]}

        assert client.hs_codes.search("t-shirt", destination_country="CA", max_results=5)[0]["code"] == "6109.10"
        assert client.hs_codes.lookup("6109.10")["code"] == "6109.10"
        assert client.hs_codes.estimate_landed_cost(request)["totalLandedCost"] == 12.0
        assert sent(2) == request


class TestInsurance:
    @responses.activate
    def test_quote_purchase_claim_and_void_match_the_gateway(self, client):
        responses.add(responses.POST, f"{WS}/insurance/quote", json={"success": True})
        responses.add(responses.POST, f"{WS}/insurance/policies", json={"success": True}, status=201)
        responses.add(responses.POST, f"{WS}/insurance/claims", json={"success": True}, status=201)
        responses.add(responses.DELETE, f"{WS}/insurance/policies/pol-1", json={"success": True})
        responses.add(responses.GET, f"{WS}/insurance/providers", json={"success": True})

        client.insurance.get_quote(carrier_code="USPS", declared_value=150, tracking_number="9400")
        client.insurance.purchase(tracking_number="9400", carrier_code="USPS", declared_value=150,
                                  coverage_tier="Standard")
        client.insurance.file_claim("pol-1", claim_reason="Lost", claim_amount=150, evidence_json="[]")
        client.insurance.void("pol-1")
        client.insurance.get_providers()

        assert sent(0) == {"declaredValue": 150, "carrierCode": "USPS", "trackingNumber": "9400"}
        assert sent(1) == {"trackingNumber": "9400", "carrierCode": "USPS", "declaredValue": 150,
                           "coverageTier": "Standard"}
        assert sent(2) == {"policyId": "pol-1", "claimReason": "Lost", "claimAmount": 150, "evidenceJson": "[]"}
        assert len(responses.calls) == 5


class TestReturns:
    @responses.activate
    def test_list_filters_by_date_range(self, client):
        responses.add(responses.GET, f"{WS}/returns", json={"success": True, "data": []},
                      match=[responses.matchers.query_param_matcher(
                          {"startDate": "2026-10-01", "endDate": "2026-10-19", "page": "1", "pageSize": "50"})])

        client.returns.list(start_date="2026-10-01", end_date="2026-10-19", page=1, page_size=50)

        assert len(responses.calls) == 1

    @responses.activate
    def test_create_posts_a_numeric_order_id_to_rma(self, client):
        responses.add(responses.POST, f"{WS}/returns/rma", json={"success": True, "data": {"rmaNumber": "R-1"}},
                      status=201)

        result = client.returns.create(order_id="42", reason="Damaged", items=[{"sku": "SKU-1", "quantity": 1}],
                                       customer_email="c@example.test")

        assert result["data"]["rmaNumber"] == "R-1"
        assert sent() == {"orderId": 42, "reason": "Damaged", "items": [{"sku": "SKU-1", "quantity": 1}],
                          "customerEmail": "c@example.test"}

    @responses.activate
    def test_generate_label_sends_the_rate_indicator(self, client):
        responses.add(responses.POST, f"{WS}/returns/RMA-1/label", json={"success": True})

        client.returns.generate_label("RMA-1", carrier_code="usps", service_type="PRIORITY", rate_indicator="FS")

        assert sent() == {"carrierCode": "usps", "serviceType": "PRIORITY", "rateIndicator": "FS"}

    @responses.activate
    def test_mark_received_sends_inspected_items(self, client):
        responses.add(responses.POST, f"{WS}/returns/17/receive", json={"success": True})
        items = [{"partNumber": "SKU-1", "quantity": 1, "disposition": 0}]

        client.returns.mark_received(17, rma_number="RMA-1", warehouse_id=3, inspected_items=items)

        assert sent() == {"rmaNumber": "RMA-1", "warehouseId": 3, "inspectedItems": items}

    def test_portal_only_return_decisions_are_gone(self, client):
        for name in ("approve", "reject", "cancel", "process_refund"):
            assert not hasattr(client.returns, name), name


class TestRules:
    @responses.activate
    def test_reorder_posts_rule_priorities(self, client):
        responses.add(responses.POST, f"{WS}/shipping-rules/reorder", json={"success": True})

        client.rules.reorder(["r-1", "r-2"])
        client.rules.reorder([{"ruleId": "r-2", "priority": 5}])

        assert sent(0) == {"rules": [{"ruleId": "r-1", "priority": 0}, {"ruleId": "r-2", "priority": 1}]}
        assert sent(1) == {"rules": [{"ruleId": "r-2", "priority": 5}]}

    @responses.activate
    def test_test_dry_runs_the_rules(self, client):
        responses.add(responses.POST, f"{WS}/shipping-rules/test", json={"success": True})

        client.rules.test({"destinationCountry": "US", "weightOz": 12})

        assert sent() == {"destinationCountry": "US", "weightOz": 12}

    @responses.activate
    def test_delete_returns_none_for_the_204(self, client):
        responses.add(responses.DELETE, f"{WS}/shipping-rules/r-1", status=204)

        assert client.rules.delete("r-1") is None
        assert responses.calls[0].request.method == "DELETE"
        assert responses.calls[0].request.url == f"{WS}/shipping-rules/r-1"


class TestDeleteReturnTypes:
    """Deletes the Gateway answers with 204 No Content are annotated ``None``, not a response envelope."""

    @pytest.mark.parametrize("method", [WebhooksResource.delete, RulesResource.delete])
    def test_204_deletes_are_annotated_none(self, method):
        assert get_type_hints(method)["return"] is type(None)


class TestPickups:
    @responses.activate
    def test_list_reads_scheduled_pickups(self, client):
        responses.add(responses.GET, f"{WS}/pickups/scheduled", json={"success": True, "data": []})

        assert client.pickups.list()["success"] is True

    @responses.activate
    def test_get_and_cancel_pass_the_carrier_code(self, client):
        responses.add(responses.GET, f"{WS}/pickups/p-1", json={"success": True},
                      match=[responses.matchers.query_param_matcher({"carrierCode": "fedex"})])
        responses.add(responses.DELETE, f"{WS}/pickups/p-1", json={"success": True},
                      match=[responses.matchers.query_param_matcher({"carrierCode": "fedex"})])
        responses.add(responses.GET, f"{WS}/pickups/p-2", json={"success": True},
                      match=[responses.matchers.query_param_matcher({})])

        client.pickups.get("p-1", carrier_code="fedex")
        client.pickups.cancel("p-1", carrier_code="fedex")
        client.pickups.get("p-2")

        assert len(responses.calls) == 3

    @responses.activate
    def test_schedule_sends_the_request_as_given(self, client):
        responses.add(responses.POST, f"{WS}/pickups", json={"success": True})
        request = {"carrierCode": "usps", "pickupDate": "2026-10-20", "street": "1 Main St", "city": "NYC",
                   "state": "NY", "postalCode": "10001", "packageCount": 2}

        client.pickups.schedule(request)

        assert sent() == request


class TestWorkspaces:
    @responses.activate
    def test_roles_are_sent_as_numbers(self, client):
        from flexops import WorkspaceRole

        responses.add(responses.POST, f"{WS}/members/invite", json={"success": True}, status=201)
        responses.add(responses.PUT, f"{WS}/members/u-1/role", json={"success": True})

        client.workspaces.invite_member("a@example.test")
        client.workspaces.invite_member("b@example.test", "Admin")
        client.workspaces.invite_member("c@example.test", WorkspaceRole.MERCHANT)
        client.workspaces.update_member_role("u-1", "owner")

        assert sent(0) == {"email": "a@example.test", "role": 2}
        assert sent(1) == {"email": "b@example.test", "role": 1}
        assert sent(2) == {"email": "c@example.test", "role": 3}
        assert sent(3) == {"newRole": 0}

    def test_unknown_role_is_refused_before_any_request(self, client):
        with pytest.raises(ValueError, match="Guest"):
            client.workspaces.invite_member("a@example.test", "Guest")

    def test_portal_only_workspace_calls_are_gone(self, client):
        assert not hasattr(client.workspaces, "create")
        assert not hasattr(client.workspaces, "update")


class TestWebhooks:
    @responses.activate
    def test_test_sends_a_test_event(self, client):
        responses.add(responses.POST, f"{WS}/webhooks/wh-1/test", json={"success": True})

        assert client.webhooks.test("wh-1")["success"] is True

    def test_get_is_gone(self, client):
        assert not hasattr(client.webhooks, "get")


class TestCarbonOffsets:
    @responses.activate
    def test_every_route_is_workspace_scoped(self, client):
        base = f"{WS}/carbon-offsets"
        responses.add(responses.POST, f"{base}/quote", json={"success": True})
        responses.add(responses.POST, f"{base}/purchase", json={"success": True}, status=201)
        responses.add(responses.GET, base, json={"success": True},
                      match=[responses.matchers.query_param_matcher({"page": "2", "pageSize": "10"})])
        responses.add(responses.GET, f"{base}/off-1", json={"success": True})
        responses.add(responses.GET, f"{base}/summary", json={"success": True})
        responses.add(responses.GET, f"{base}/settings", json={"success": True})
        responses.add(responses.PUT, f"{base}/settings", json={"success": True})

        client.carbon_offsets.quote(weight_lbs=2.5, distance_miles=800)
        client.carbon_offsets.purchase(tracking_number="9400", weight_lbs=2.5, distance_miles=800,
                                       idempotency_key="offset-001")
        client.carbon_offsets.list(page=2, page_size=10)
        client.carbon_offsets.get("off-1")
        client.carbon_offsets.get_summary()
        client.carbon_offsets.get_settings()
        client.carbon_offsets.update_settings(auto_offset_enabled=True)

        assert sent(0) == {"weightLbs": 2.5, "distanceMiles": 800}
        assert sent(1) == {"trackingNumber": "9400", "weightLbs": 2.5, "distanceMiles": 800}
        assert responses.calls[1].request.headers["Idempotency-Key"] == "offset-001"
        assert sent(6) == {"autoOffsetEnabled": True}
        assert len(responses.calls) == 7


class TestProxyResources:
    def test_proxy_writes_are_gone(self, client):
        assert not hasattr(client.orders, "create")
        assert not hasattr(client.orders, "cancel")
        assert not hasattr(client.inventory, "post_asn_receipt")
        assert not hasattr(client.inventory, "update_inventory")

    def test_portal_only_auth_calls_are_gone(self, client):
        for name in ("register", "get_profile", "update_profile", "change_password", "forgot_password",
                     "reset_password", "verify_email"):
            assert not hasattr(client.auth, name), name


class TestRecurringShipments:
    """Bare JSON responses; pause/resume/trigger/delete answer 204."""

    @responses.activate
    def test_routes_bodies_and_responses(self, client):
        from flexops import RecurrenceInterval

        base = f"{WS}/recurring-shipments"
        item = {"id": "rs-1", "name": "Weekly restock", "interval": 1, "isActive": True}
        responses.add(responses.GET, base, json=[item])
        responses.add(responses.GET, f"{base}/rs-1", json=item)
        responses.add(responses.POST, base, json=item, status=201)
        responses.add(responses.PUT, f"{base}/rs-1", json=item)
        responses.add(responses.DELETE, f"{base}/rs-1", status=204)
        for action in ("pause", "resume", "trigger"):
            responses.add(responses.POST, f"{base}/rs-1/{action}", status=204)
        create = {"name": "Weekly restock", "interval": RecurrenceInterval.WEEKLY, "addressId": "addr-1",
                  "firstRunUtc": "2026-10-20T09:00:00Z"}

        assert client.recurring_shipments.list() == [item]
        assert client.recurring_shipments.get("rs-1") == item
        assert client.recurring_shipments.create(create) == item
        assert client.recurring_shipments.update("rs-1", {"maxFailures": 5}) == item
        assert client.recurring_shipments.delete("rs-1") is None
        assert client.recurring_shipments.pause("rs-1") is None
        assert client.recurring_shipments.resume("rs-1") is None
        assert client.recurring_shipments.trigger("rs-1", idempotency_key="run-001") is None

        assert sent(2) == {**create, "interval": 1}
        assert sent(3) == {"maxFailures": 5}
        assert responses.calls[5].request.body is None
        assert responses.calls[7].request.headers["Idempotency-Key"] == "run-001"


class TestReportSchedules:
    """Envelope responses, except delete (204)."""

    @responses.activate
    def test_routes_bodies_and_responses(self, client):
        from flexops import ReportFormat, ReportFrequency

        base = f"{WS}/report-schedules"
        item = {"id": "rpt-1", "reportType": "shipments", "format": 0, "frequencyType": 1, "isEnabled": True}
        responses.add(responses.GET, base, json={"success": True, "data": [item]})
        responses.add(responses.GET, f"{base}/rpt-1", json={"success": True, "data": item})
        responses.add(responses.POST, base, json={"success": True, "data": item}, status=201)
        responses.add(responses.PUT, f"{base}/rpt-1", json={"success": True, "data": item})
        responses.add(responses.DELETE, f"{base}/rpt-1", status=204)
        responses.add(responses.POST, f"{base}/rpt-1/toggle", json={"success": True, "data": None})
        create = {"reportType": "shipments", "format": ReportFormat.CSV, "frequencyType": ReportFrequency.WEEKLY,
                  "dayOfWeek": 1, "timeOfDayUtc": "08:00:00", "recipientEmails": "ops@example.test"}

        assert client.report_schedules.list()["data"] == [item]
        assert client.report_schedules.get("rpt-1")["data"] == item
        assert client.report_schedules.create(create)["data"] == item
        assert client.report_schedules.update("rpt-1", {"isEnabled": False})["data"] == item
        assert client.report_schedules.delete("rpt-1") is None
        assert client.report_schedules.toggle("rpt-1") == {"success": True, "data": None}

        assert sent(2) == {**create, "format": 0, "frequencyType": 1}
        assert sent(3) == {"isEnabled": False}


class TestEmailTemplates:
    """Bare JSON responses; PUT upserts by eventType."""

    @responses.activate
    def test_routes_bodies_and_responses(self, client):
        from flexops import TrackingEmailEvent

        base = f"{WS}/email-templates"
        item = {"id": "tpl-1", "eventType": 3, "eventTypeName": "Delivered", "isEnabled": True}
        responses.add(responses.GET, base, json=[item])
        responses.add(responses.GET, f"{base}/tpl-1", json=item)
        responses.add(responses.PUT, base, json=item)
        responses.add(responses.DELETE, f"{base}/tpl-1", status=204)
        responses.add(responses.POST, f"{base}/preview",
                      json={"renderedSubject": "Delivered", "renderedHtmlBody": "<p>Hi</p>"})
        upsert = {"eventType": TrackingEmailEvent.DELIVERED, "subjectTemplate": "Delivered",
                  "htmlBodyTemplate": "<p>{{trackingNumber}}</p>"}

        assert client.email_templates.list() == [item]
        assert client.email_templates.get("tpl-1") == item
        assert client.email_templates.upsert(upsert) == item
        assert client.email_templates.delete("tpl-1") is None
        preview = client.email_templates.preview(subject_template="Delivered", html_body_template="<p>Hi</p>")

        assert preview["renderedSubject"] == "Delivered"
        assert sent(2) == {**upsert, "eventType": 3}
        assert sent(4) == {"subjectTemplate": "Delivered", "htmlBodyTemplate": "<p>Hi</p>"}
