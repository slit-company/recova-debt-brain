from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

from trustgraph_legal.document_assembly import build_document_assembly

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
PAGES_FIXTURE: Final = REPO_ROOT / "tests" / "fixtures" / "legal-ocr-pages"
REAL_OCR_ROOT: Final = Path("/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630")
ROUTE_RESOURCES: Final = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v0.json"
LEGAL_SOURCES: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_route_sources_v0.json"
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


def test_writes_redacted_full_graph_when_assembly_json_is_provided(tmp_path: Path) -> None:
    # Given: a full synthetic DocumentAssembly JSON payload and route resources.
    assembly_path = tmp_path / "assembly.json"
    output_path = tmp_path / "debtor-context-full.json"
    _ = assembly_path.write_text(
        json.dumps(build_document_assembly(PAGES_FIXTURE, REPO_ROOT).to_json(), ensure_ascii=False),
        encoding="utf-8",
    )

    # When: the debtor context CLI builds the graph from that assembly.
    result = _run_cli(
        "--assembly",
        str(assembly_path),
        "--out",
        str(output_path),
        "--route-resources",
        str(ROUTE_RESOURCES),
        "--legal-sources",
        str(LEGAL_SOURCES),
    )

    # Then: the observable output is a redacted graph with route candidates and snapshot route ids.
    assert result.returncode == 0, result.stderr
    payload = _json(output_path)
    summary = _json_object(payload["summary"])
    snapshot = _json_object(payload["graph_snapshot"])
    assert payload["schema_version"] == "recova-debtor-context-graph/v1"
    assert payload["pii_profile"] == {"raw_text_included": False, "source_text_included": False}
    assert summary["document_pages"] == 5
    assert _number(summary["route_candidates"]) > 0
    assert _json_list(snapshot["route_candidate_ids"])
    bank_route = next(
        route
        for item in _json_list(payload["route_candidates"])
        if (route := _json_object(item))["route_id"] == "bank_account_attachment"
    )
    assert bank_route["status"] == "possible"
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "Synthetic OCR Page" not in encoded
    assert "[DEBTOR_PERSON_REDACTED]" not in encoded


def test_writes_stable_snapshot_ids_for_equivalent_assembly_inputs(tmp_path: Path) -> None:
    # Given: the same synthetic DocumentAssembly JSON payload is used twice.
    assembly_path = tmp_path / "assembly.json"
    first_output = tmp_path / "first-debtor-context.json"
    second_output = tmp_path / "second-debtor-context.json"
    _ = assembly_path.write_text(
        json.dumps(build_document_assembly(PAGES_FIXTURE, REPO_ROOT).to_json(), ensure_ascii=False),
        encoding="utf-8",
    )

    # When: the debtor context CLI builds the graph from equivalent inputs.
    for output_path in (first_output, second_output):
        result = _run_cli(
            "--assembly",
            str(assembly_path),
            "--out",
            str(output_path),
            "--route-resources",
            str(ROUTE_RESOURCES),
            "--legal-sources",
            str(LEGAL_SOURCES),
        )
        assert result.returncode == 0, result.stderr

    # Then: graph and replay snapshot identifiers are stable.
    first = _json(first_output)
    second = _json(second_output)
    first_summary = _json_object(first["summary"])
    second_summary = _json_object(second["summary"])
    first_snapshot = _json_object(first["graph_snapshot"])
    second_snapshot = _json_object(second["graph_snapshot"])
    assert first["graph_snapshot_id"] == second["graph_snapshot_id"]
    assert first_summary["snapshot_replay_id"] == second_summary["snapshot_replay_id"]
    assert first_snapshot["route_candidate_ids"] == second_snapshot["route_candidate_ids"]


def test_writes_pii_safe_real_ocr_summary_when_ocr_root_is_provided(tmp_path: Path) -> None:
    if not REAL_OCR_ROOT.is_dir():
        pytest.skip("real OCR corpus is not available on this machine")
    # Given: the local real OCR corpus and summary-only mode.
    output_path = tmp_path / "real-ocr-summary.json"

    # When: the CLI processes a bounded real OCR sample without writing page text.
    result = _run_cli(
        "--ocr-root",
        str(REAL_OCR_ROOT),
        "--out",
        str(output_path),
        "--summary-only",
        "--limit",
        "3",
    )

    # Then: the output is aggregate-only and preserves the redaction contract.
    assert result.returncode == 0, result.stderr
    payload = _json(output_path)
    summary = _json_object(payload["summary"])
    assert "document_pages" not in payload
    assert "fact_assertions" not in payload
    assert payload["pii_profile"] == {"raw_text_included": False, "source_text_included": False}
    assert summary["document_pages"] == 3
    assert _number(summary["route_candidates"]) > 0
    assert _text(summary["snapshot_replay_id"]).startswith("snapshot-replay:")
    assert isinstance(summary["route_status_counts"], dict)


def test_unknown_only_ocr_root_emits_review_summary(tmp_path: Path) -> None:
    # Given: an OCR root with only unknown markdown fragments.
    ocr_root = tmp_path / "unknown-only"
    pages_dir = ocr_root / "loose"
    pages_dir.mkdir(parents=True)
    _ = (pages_dir / "page_001.md").write_text(
        "# Low confidence fragment\nClassifier hint: review required\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "unknown-only.json"

    # When: the CLI builds a summary from unknown-only OCR.
    result = _run_cli(
        "--ocr-root",
        str(ocr_root),
        "--out",
        str(output_path),
        "--summary-only",
    )

    # Then: unknown assemblies and graph review items are surfaced without raw text.
    assert result.returncode == 0, result.stderr
    payload = _json(output_path)
    summary = _json_object(payload["summary"])
    route_status_counts = _json_object(summary["route_status_counts"])
    pii_profile = _json_object(payload["pii_profile"])
    assert summary["unknown_assemblies"] == 1
    assert _number(summary["review_items"]) >= 1
    assert _number(route_status_counts["missing_facts"]) > 0
    assert pii_profile["raw_text_included"] is False
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "Low confidence fragment" not in encoded


def test_reports_controlled_error_when_ocr_root_is_missing(tmp_path: Path) -> None:
    # Given: a missing OCR root path.
    output_path = tmp_path / "missing.json"

    # When: the CLI is invoked with that invalid root.
    result = _run_cli(
        "--ocr-root",
        str(tmp_path / "does-not-exist"),
        "--out",
        str(output_path),
    )

    # Then: it exits with a controlled code and does not leave partial output.
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "OCR root not found" in result.stderr
    assert not output_path.exists()


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "trustgraph_legal.debtor_context", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _json(path: Path) -> JsonObject:
    return _json_object(json.loads(path.read_text(encoding="utf-8")))


def _json_object(value: JsonValue) -> JsonObject:
    assert isinstance(value, dict)
    return value


def _json_list(value: JsonValue) -> list[JsonValue]:
    assert isinstance(value, list)
    return value


def _number(value: JsonValue) -> int | float:
    assert isinstance(value, (int, float)) and not isinstance(value, bool)
    return value


def _text(value: JsonValue) -> str:
    assert isinstance(value, str)
    return value
