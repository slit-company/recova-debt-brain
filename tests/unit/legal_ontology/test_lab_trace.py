from __future__ import annotations

import json
from pathlib import Path

from trustgraph_legal.lab_trace import (
    TraceInvocation,
    evaluation_run_row,
    fake_supabase_payload,
    judgment_run_row,
    linked_tool_trace_row,
    rows_for_fixture_manifest,
    tool_trace_row,
)


def test_tool_trace_row_hashes_and_redacts_arguments() -> None:
    national_id = "900101" + "-" + "1234567"
    phone = "010-" + "1234-" + "5678"
    sensitive_label = "resident " + "id"
    row = tool_trace_row(
        TraceInvocation(
            tool_name="check_case_stop_gates",
            arguments={
                "memo": "{} {} phone {}".format(
                    sensitive_label,
                    national_id,
                    phone,
                ),
            },
            envelope={
                "tool_name": "check_case_stop_gates",
                "group": "stopgate",
                "scope": "stopgate:check",
                "source_refs": ["fixture://case#line-1"],
                "warnings": [],
                "result": {
                    "decision": "보류",
                    "confidence": 0.84,
                    "failure_labels": ["limitation_risk"],
                },
            },
            latency_ms=3,
        )
    )

    encoded = json.dumps(row, ensure_ascii=False, sort_keys=True)
    assert len(str(row["arguments_hash_sha256"])) == 64
    assert len(str(row["envelope_hash_sha256"])) == 64
    assert sensitive_label not in encoded
    assert national_id not in encoded
    assert phone not in encoded
    assert row["status"] == "ok"
    assert row["source_refs"] == ["fixture://case#line-1"]


def test_rows_for_fixture_manifest_create_fake_supabase_contract() -> None:
    rows = rows_for_fixture_manifest(
        Path("tests/fixtures/legal-ocr/manifest.json"),
        Path.cwd(),
    )
    output = fake_supabase_payload(rows)

    assert output["mode"] == "fake_supabase"
    assert output["row_count"] == 3
    assert output["raw_text_included"] is False
    assert "check_case_stop_gates" in output["summary"]["tool_names"]
    assert all(row["redacted_arguments"] for row in rows[1:])


def test_judgment_trace_rows_link_evaluation_judgment_and_tool_trace() -> None:
    sensitive_label = "resident " + "id"
    national_id = "900101" + "-" + "1234567"
    invocation = TraceInvocation(
        tool_name="check_case_stop_gates",
        arguments={"memo": "{} {}".format(sensitive_label, national_id)},
        envelope={
            "tool_name": "check_case_stop_gates",
            "group": "stopgate",
            "scope": "stopgate:check",
            "source_refs": ["fixture://case#line-1"],
            "warnings": [],
            "result": {
                "decision": "보류",
                "confidence": 0.84,
                "risk_flags": ["limitation_risk"],
                "recommended_action": "Hold for review.",
            },
        },
        latency_ms=4,
    )

    evaluation = evaluation_run_row(invocation, "mcp-smoke-test-run", 16)
    judgment = judgment_run_row(invocation, "eval-id")
    trace = linked_tool_trace_row(invocation, "eval-id", "judgment-id")

    encoded = json.dumps(
        {"evaluation": evaluation, "judgment": judgment, "trace": trace},
        ensure_ascii=False,
        sort_keys=True,
    )
    assert evaluation["run_ref"] == "mcp-smoke-test-run"
    assert evaluation["tool_count"] == 16
    assert judgment["evaluation_run_id"] == "eval-id"
    assert judgment["decision"] == "보류"
    assert judgment["confidence"] == 0.84
    assert judgment["failure_labels"] == ["limitation_risk"]
    assert trace["evaluation_run_id"] == "eval-id"
    assert trace["judgment_run_id"] == "judgment-id"
    assert national_id not in encoded
    assert sensitive_label not in encoded
