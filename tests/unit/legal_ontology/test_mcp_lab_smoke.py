from __future__ import annotations

import pytest

from scripts.recova_mcp import mcp_lab_smoke


def test_auth_failure_detection_accepts_only_auth_marked_errors() -> None:
    auth_error = RuntimeError("HTTP 401 Unauthorized: missing bearer token")
    dns_error = ConnectionError("temporary failure in name resolution")

    auth_details = mcp_lab_smoke.auth_error_details(auth_error)
    dns_details = mcp_lab_smoke.auth_error_details(dns_error)

    assert auth_details.auth_rejected is True
    assert "Unauthorized" in auth_details.summary
    assert dns_details.auth_rejected is False


def test_success_validation_requires_recorded_trace_judgment_and_evaluation() -> None:
    result = {
        "status": "ok",
        "tool_count": 16,
        "generic_tools": [],
        "execution_tools": [],
        "decision": "보류",
        "trace_status": "recorded",
        "evaluation_status": "not_recorded",
        "judgment_status": "recorded",
        "trace_required": True,
    }

    with pytest.raises(RuntimeError, match="evaluation trace not recorded"):
        mcp_lab_smoke.validate_result(result, expect_auth_failure=False)


def test_success_validation_allows_missing_trace_only_when_explicit() -> None:
    result = {
        "status": "ok",
        "tool_count": 16,
        "generic_tools": [],
        "execution_tools": [],
        "decision": "보류",
        "trace_status": "not_recorded",
        "evaluation_status": "not_recorded",
        "judgment_status": "not_recorded",
        "trace_required": False,
    }

    mcp_lab_smoke.validate_result(result, expect_auth_failure=False)
