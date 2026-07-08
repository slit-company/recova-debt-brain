from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from trustgraph_legal.debtor_context_types import JsonObject, JsonValue


@dataclass(frozen=True, slots=True)
class WorkflowExpectation:
    scenario_id: str
    stage: str
    action: str
    posture: str
    remediation_loop: str


REQUIRED_SEMIREAL_SCENARIOS: Final = (
    "premature_litigation_review",
    "evidence_completion_loop",
    "title_acquisition_loop",
    "asset_discovery_loop",
    "enforcement_ready_review",
    "monitoring_low_yield",
    "finance_reconciliation_hold",
    "insolvency_protected_asset_hold",
)


def workflow_expectations(bundle: JsonObject) -> dict[str, WorkflowExpectation]:
    expectations: dict[str, WorkflowExpectation] = {}
    for entry in _objects(bundle.get("scenarios")):
        expectation = _expectation(entry)
        if expectation is not None:
            expectations[expectation.scenario_id] = expectation
    return expectations


def _expectation(entry: JsonObject) -> WorkflowExpectation | None:
    stage = _text(entry.get("expected_workflow_stage"))
    if not stage:
        return None
    return WorkflowExpectation(
        scenario_id=_text(entry.get("scenario_id")),
        stage=stage,
        action=_text(entry.get("expected_workflow_action")),
        posture=_text(entry.get("expected_workflow_posture")),
        remediation_loop=_text(entry.get("expected_workflow_remediation_loop")),
    )


def _objects(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""
