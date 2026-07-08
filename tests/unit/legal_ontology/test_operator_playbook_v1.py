from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypeAlias

from scripts.legal_ontology.domain_sources_v1_common import load_json


REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK_PATH = REPO_ROOT / "resources" / "workflows" / "debt_collection_operator_playbook_v1.json"
WORKFLOW_PATH = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_operator_playbook_v1.py"
REQUIRED_STAGE_IDS = (
    "intake",
    "evidence_completion",
    "title_acquisition",
    "asset_discovery",
    "execution_route_selection",
    "enforcement_ready",
    "monitoring",
    "settlement_restructuring",
    "insolvency_protected_asset_review",
    "closure",
)
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def load_json_object(path: Path) -> JsonObject:
    return load_json(path)


def object_list(entry: JsonObject, field: str) -> list[JsonObject]:
    value = entry[field]
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def string_list_field(entry: JsonObject, field: str) -> list[str]:
    value = entry[field]
    assert isinstance(value, list)
    strings: list[str] = []
    for item in value:
        assert isinstance(item, str)
        strings.append(item)
    return strings


def run_validator(playbook_path: Path = PLAYBOOK_PATH) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            str(playbook_path),
            str(WORKFLOW_PATH),
            str(SOURCES_PATH),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_operator_playbook_v1() -> None:
    # Given: the v1 collection operator playbook and its workflow/source dependencies.
    result = run_validator()

    # When: the CLI validator checks operator-stage structure and references.
    assert result.returncode == 0

    # Then: every practical workflow stage is counted under advisory-only semantics.
    assert "PASS operator_playbook recova-debt-collection-operator-playbook@v1.0.0" in result.stdout
    assert "stages=10" in result.stdout
    assert "action_types=" in result.stdout
    assert "remediation_loops=" in result.stdout


def test_playbook_models_operator_stage_judgment() -> None:
    # Given: the committed operator playbook resource.
    playbook = load_json_object(PLAYBOOK_PATH)
    stages = object_list(playbook, "stages")

    # When: stage entries are indexed by stable ids.
    by_id = {str(stage["stage_id"]): stage for stage in stages}

    # Then: the playbook covers the practical collection workflow and separates support checkpoints.
    assert tuple(by_id) == REQUIRED_STAGE_IDS
    assert playbook["direct_execution_allowed"] is False
    assert playbook["no_direct_execution"] is True
    assert playbook["non_execution_semantics"] == "advisory_only_human_review_required"
    for stage_id in REQUIRED_STAGE_IDS:
        stage = by_id[stage_id]
        assert stage["human_review_required"] is True
        assert stage["non_execution_semantics"] == "advisory_only_human_review_required"
        assert string_list_field(stage, "workflow_state_ids")
        assert string_list_field(stage, "next_action_types")
        assert string_list_field(stage, "premature_action_reasons")
        assert string_list_field(stage, "required_checkpoint_inputs")
        assert string_list_field(stage, "remediation_loops")
        assert string_list_field(stage, "source_refs")


def test_validator_rejects_unknown_workflow_state(tmp_path: Path) -> None:
    # Given: a generated playbook copy with a stage pointing outside the workflow resource.
    playbook = load_json_object(PLAYBOOK_PATH)
    stages = object_list(playbook, "stages")
    stages[0]["workflow_state_ids"] = ["missing_workflow_state"]
    invalid_path = tmp_path / "invalid-operator-playbook.json"
    _ = invalid_path.write_text(json.dumps(playbook, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated invalid resource.
    result = run_validator(invalid_path)

    # Then: it rejects the unknown workflow state before downstream engines can use it.
    assert result.returncode != 0
    assert "missing_workflow_state" in result.stderr
    assert "unknown workflow_state_id" in result.stderr


def test_validator_rejects_execution_semantics(tmp_path: Path) -> None:
    # Given: a generated playbook copy that tries to authorize direct collection action.
    playbook = load_json_object(PLAYBOOK_PATH)
    playbook["direct_execution_allowed"] = True
    invalid_path = tmp_path / "execution-operator-playbook.json"
    _ = invalid_path.write_text(json.dumps(playbook, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated invalid resource.
    result = run_validator(invalid_path)

    # Then: it rejects the playbook as an executable action surface.
    assert result.returncode != 0
    assert "direct_execution_allowed must be false" in result.stderr
