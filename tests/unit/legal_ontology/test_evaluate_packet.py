from __future__ import annotations

import json
from pathlib import Path

from scripts.legal_ontology.evaluate_packet import main


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_MANIFEST = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "manifest.json"


def test_evaluator_can_write_qa_artifact_outside_repo(tmp_path: Path) -> None:
    output_path = tmp_path / "task-10-eval.json"

    exit_code = main(
        [
            "--fixtures",
            str(FIXTURE_MANIFEST),
            "--out",
            str(output_path),
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["summary"]["status"] == "passed"
    assert payload["summary"]["tool_count"] == 16
    trace = payload["judgment_trace"]
    assert trace["decision"] in {"가능", "불가능", "보류"}
    assert isinstance(trace["confidence"], float)
    assert trace["source_refs"]
    assert trace["failure_labels"]
    assert trace["expected_answer"]["decision"] == "보류"
    assert trace["expected_answer"]["recommendation"] == "hold_for_review"
    assert trace["actual_answer"]["decision"] == payload["summary"]["decision"]
    assert trace["actual_answer"]["recommendation"] == payload["summary"]["recommendation"]
    assert trace["correction_status"] == "pending_human_review"
