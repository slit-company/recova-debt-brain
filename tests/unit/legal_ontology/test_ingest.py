from __future__ import annotations

import json
import zipfile
from pathlib import Path

from trustgraph_legal.ingest import main
from trustgraph_legal.registry import RegistryOptions, collect_registry_payload


def _write_zip(path: Path, entries: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, text in entries.items():
            archive.writestr(name, text)


def test_duplicate_content_becomes_duplicate_status_when_seen_twice(
    tmp_path: Path,
) -> None:
    zip_path = tmp_path / "dupes.zip"
    content = "문서 표식: 지급명령\n사건: 2024차전1010\n청구: [CLAIM_TOKEN]\n"
    _write_zip(
        zip_path,
        {
            "markdown_flat/a.md": content,
            "markdown_flat/b.md": content,
        },
    )

    payload = collect_registry_payload(zip_path, RegistryOptions(limit=10))

    records = payload.to_json()["records"]
    assert isinstance(records, list)
    assert records[0]["registry_status"] == "dry_run_insert_candidate"
    assert records[1]["registry_status"] == "duplicate"
    assert records[1]["duplicate_of_document_id"] == records[0]["document_id"]


def test_cli_writes_redacted_evidence_when_sensitive_shapes_exist(
    tmp_path: Path,
) -> None:
    zip_path = tmp_path / "safe.zip"
    evidence_path = tmp_path / "evidence.json"
    sensitive_number = "900101" + "-1234567"
    sensitive_phone = "010" + "-1234" + "-5678"
    content = (
        "문서 표식: 채권압류 및 추심명령\n"
        "사건: 2025타채7777\n"
        f"식별값: {sensitive_number}\n"
        f"전화: {sensitive_phone}\n"
    )
    _write_zip(zip_path, {"markdown_flat/one.md": content})

    exit_code = main(
        [
            "--zip",
            str(zip_path),
            "--dry-run",
            "--limit",
            "1",
            "--evidence",
            str(evidence_path),
        ]
    )

    evidence = evidence_path.read_text(encoding="utf-8")
    payload = json.loads(evidence)
    assert exit_code == 0
    assert payload["summary"]["records"] == 1
    assert sensitive_number not in evidence
    assert sensitive_phone not in evidence
    assert payload["records"][0]["pii_profile"]["raw_text_included"] is False
