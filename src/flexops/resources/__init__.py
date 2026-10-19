# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from .analytics import AnalyticsResource
from .auth import AuthResource
from .carbon_offsets import CarbonOffsetsResource
from .carriers import CarriersResource
from .email_templates import EmailTemplatesResource
from .hs_codes import HsCodesResource
from .insurance import InsuranceResource
from .inventory import InventoryResource
from .orders import OrdersResource
from .pickups import PickupsResource
from .recurring_shipments import RecurringShipmentsResource
from .report_schedules import ReportSchedulesResource
from .returns import ReturnsResource
from .rules import RulesResource
from .scan_forms import ScanFormsResource
from .shipping import ShippingResource
from .wallet import WalletResource
from .webhooks import WebhooksResource
from .workspaces import WorkspacesResource

__all__ = [
    "AnalyticsResource",
    "AuthResource",
    "CarbonOffsetsResource",
    "CarriersResource",
    "EmailTemplatesResource",
    "HsCodesResource",
    "InsuranceResource",
    "InventoryResource",
    "OrdersResource",
    "PickupsResource",
    "RecurringShipmentsResource",
    "ReportSchedulesResource",
    "ReturnsResource",
    "RulesResource",
    "ScanFormsResource",
    "ShippingResource",
    "WalletResource",
    "WebhooksResource",
    "WorkspacesResource",
]
