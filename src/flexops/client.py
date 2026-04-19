# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations

from ._http import HttpClient
from ._types import FlexOpsConfig
from .resources.analytics import AnalyticsResource
from .resources.api_keys import ApiKeysResource
from .resources.auth import AuthResource
from .resources.carriers import CarriersResource
from .resources.email_templates import EmailTemplatesResource
from .resources.hs_codes import HsCodesResource
from .resources.insurance import InsuranceResource
from .resources.inventory import InventoryResource
from .resources.offsets import OffsetsResource
from .resources.orders import OrdersResource
from .resources.pickups import PickupsResource
from .resources.recurring_shipments import RecurringShipmentsResource
from .resources.reports import ReportsResource
from .resources.returns import ReturnsResource
from .resources.rules import RulesResource
from .resources.scan_forms import ScanFormsResource
from .resources.shipping import ShippingResource
from .resources.wallet import WalletResource
from .resources.webhooks import WebhooksResource
from .resources.workspaces import WorkspacesResource


class FlexOps:
    """FlexOps Platform SDK Client.

    The main entry point for interacting with the FlexOps multi-carrier
    shipping platform API.

    Example - API key authentication (recommended for server-to-server)::

        from flexops import FlexOps

        client = FlexOps(
            api_key="fxk_live_...",
            workspace_id="ws_abc123",
        )

        # Get shipping rates
        rates = client.shipping.get_rates({
            "fromZip": "10001",
            "toZip": "90210",
            "weight": 16,
            "weightUnit": "oz",
        })

    Example - Email/password authentication::

        client = FlexOps(base_url="https://gateway.flexops.io")
        client.auth.login("user@co.com", "password")

    Example - Direct carrier operations::

        # USPS domestic label
        label = client.carriers.usps.create_domestic_label({...})

        # FedEx rate quote
        rates = client.carriers.fedex.get_rates({...})
    """

    def __init__(
        self,
        *,
        base_url: str = "https://gateway.flexops.io",
        access_token: str | None = None,
        api_key: str | None = None,
        workspace_id: str | None = None,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        retry: dict | None = None,
    ) -> None:
        from ._types import RetryConfig

        config = FlexOpsConfig(
            base_url=base_url,
            access_token=access_token,
            api_key=api_key,
            workspace_id=workspace_id,
            timeout=timeout,
            headers=headers,
            retry=RetryConfig(**retry) if retry else None,
        )
        self._http = HttpClient(config)
        self._workspace_id = workspace_id

        get_ws_id = lambda: self._workspace_id  # noqa: E731

        self.auth = AuthResource(self._http)
        self.workspaces = WorkspacesResource(self._http, get_ws_id)
        self.shipping = ShippingResource(self._http, get_ws_id)
        self.carriers = CarriersResource(self._http)
        self.webhooks = WebhooksResource(self._http, get_ws_id)
        self.wallet = WalletResource(self._http, get_ws_id)
        self.insurance = InsuranceResource(self._http, get_ws_id)
        self.returns = ReturnsResource(self._http, get_ws_id)
        self.api_keys = ApiKeysResource(self._http, get_ws_id)
        self.analytics = AnalyticsResource(self._http)
        self.orders = OrdersResource(self._http)
        self.inventory = InventoryResource(self._http)
        self.pickups = PickupsResource(self._http, get_ws_id)
        self.scan_forms = ScanFormsResource(self._http, get_ws_id)
        self.rules = RulesResource(self._http, get_ws_id)
        self.offsets = OffsetsResource(self._http, get_ws_id)
        self.hs_codes = HsCodesResource(self._http, get_ws_id)
        self.recurring_shipments = RecurringShipmentsResource(self._http, get_ws_id)
        self.email_templates = EmailTemplatesResource(self._http, get_ws_id)
        self.reports = ReportsResource(self._http, get_ws_id)

    @property
    def workspace_id(self) -> str | None:
        """Get or set the active workspace ID."""
        return self._workspace_id

    @workspace_id.setter
    def workspace_id(self, value: str | None) -> None:
        self._workspace_id = value

    def set_access_token(self, token: str) -> None:
        """Set the JWT access token for authentication."""
        self._http.set_access_token(token)

    def set_api_key(self, key: str) -> None:
        """Set the API key for authentication."""
        self._http.set_api_key(key)
