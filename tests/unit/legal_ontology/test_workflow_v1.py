from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypeAlias


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
DOMAIN_SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_workflow_v1.py"
REQUIRED_STATE_IDS = (
    "intake",
    "identity_evidence_package",
    "limitation_review",
    "title_acquisition",
    "service_finality_execution_clause",
    "voluntary_recovery",
    "provisional_remedy",
    "asset_discovery",
    "execution_route_selection",
    "insolvency_discharge_review",
    "monitoring_retry",
    "closure",
)
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def load_json_object(path: Path) -> JsonObject:
    raw: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def run_validator(
    workflow_path: Path = WORKFLOW_PATH,
    sources_path: Path = DOMAIN_SOURCES_PATH,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(workflow_path), str(sources_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_collection_workflow_v1() -> None:
    # Given: the v1 collection workflow resource and frozen domain source map.
    # When: the CLI validator checks workflow structure and source references.
    result = run_validator()

    # Then: it reports every canonical state, transition, and monitoring loop.
    assert result.returncode == 0
    assert "PASS workflow recova-debt-collection-workflow@v1.0.0" in result.stdout
    assert "states=12" in result.stdout
    assert "transitions=" in result.stdout
    assert "loops=" in result.stdout


def test_workflow_resource_models_required_state_semantics() -> None:
    # Given: the workflow resource as committed for Todo 5.
    workflow = load_json_object(WORKFLOW_PATH)
    states = workflow["states"]
    assert isinstance(states, list)

    # When: states are indexed by their stable workflow ids.
    by_id = {state["state_id"]: state for state in states if isinstance(state, dict)}

    # Then: all required states carry evidence, review, and route-link separation semantics.
    assert tuple(by_id) == REQUIRED_STATE_IDS
    for state_id in REQUIRED_STATE_IDS:
        state = by_id[state_id]
        assert state["required_evidence"]
        assert state["preconditions"]
        assert state["exit_conditions"]
        assert state["review_states"]
        assert state["source_refs"]
        assert state["route_link_semantics"] == "workflow_precondition_only_no_route_decision_logic"


def test_validator_rejects_invalid_transition_target(tmp_path: Path) -> None:
    # Given: a generated workflow copy with a transition pointing to an unknown state.
    workflow = load_json_object(WORKFLOW_PATH)
    transitions = workflow["transitions"]
    assert isinstance(transitions, list)
    first_transition = transitions[0]
    assert isinstance(first_transition, dict)
    first_transition["to_state"] = "unknown_workflow_state"
    invalid_path = tmp_path / "invalid-workflow.json"
    invalid_path.write_text(json.dumps(workflow, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated invalid resource.
    result = run_validator(workflow_path=invalid_path)

    # Then: it fails with the invalid target named in diagnostics.
    assert result.returncode != 0
    assert "unknown_workflow_state" in result.stderr
    assert "unknown to_state" in result.stderr
