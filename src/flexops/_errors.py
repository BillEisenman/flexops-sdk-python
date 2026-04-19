# ***********************************************************************
# Package          : flexops
# Author           : FlexOps, LLC
# Created          : 2026-03-04
#
# Copyright (c) 2021-2026 by FlexOps, LLC. All rights reserved.
# ***********************************************************************

from __future__ import annotations


class FlexOpsError(Exception):
    """Base exception for all FlexOps SDK errors."""

    def __init__(
        self,
        message: str,
        status: int = 0,
        code: str | None = None,
        errors: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.errors = errors


class FlexOpsAuthError(FlexOpsError):
    """Raised on 401 Unauthorized responses."""

    def __init__(self, message: str = "Authentication required. Check your access token or API key.") -> None:
        super().__init__(message, status=401, code="UNAUTHORIZED")


class FlexOpsRateLimitError(FlexOpsError):
    """Raised on 429 Too Many Requests responses."""

    def __init__(self, message: str = "Rate limited.", retry_after: int | None = None) -> None:
        super().__init__(message, status=429, code="RATE_LIMITED")
        self.retry_after = retry_after
