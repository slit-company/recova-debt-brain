from __future__ import annotations

import json
from pathlib import Path

from trustgraph_legal.lab_trace import (
    TraceInvocation,
    fake_supabase_payload,
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
