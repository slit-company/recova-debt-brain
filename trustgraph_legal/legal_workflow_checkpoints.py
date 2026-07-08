from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from trustgraph_legal.stopgate_types import JsonObject, JsonValue, StopGateFinding, StopGatePayload


SCHEMA_VERSION: Final = "trustgraph-legal-workflow-checkpoints/v1"
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"
CLEARED_BY: Final = "static_stopgate_result_only"


@dataclass(frozen=True)
class CheckpointSpec:
    checkpoint_id: str
    label: str
    clear_status: str
    gate: str
    blocked: bool


@dataclass(frozen=True)
class LegalWorkflowCheckpoint:
    spec: CheckpointSpec
    findings: tuple[StopGateFinding, ...]

    def to_json(self) -> JsonObject:
        payload: JsonObject = {
            "checkpoint_id": self.spec.checkpoint_id,
            "label": self.spec.label,
            "status": _status(self.spec, self.findings),
            "workflow_gate": _workflow_gate(self.spec, self.findings),
            "reason_codes": _reason_codes(self.findings),
            "required_preconditions": _required_preconditions(self.findings),
            "missing_evidence": _missing_evidence(self.findings),
            "source_refs": _source_refs(self.findings),
            "blocks_enforcement_readiness": self.spec.blocked and bool(self.findings),
            "cleared_by": CLEARED_BY,
        }
        return payload


@dataclass(frozen=True)
class LegalWorkflowCheckpointResult:
    stopgate_payload: StopGatePayload
    checkpoints: tuple[LegalWorkflowCheckpoint, ...]

    def to_json(self) -> JsonObject:
        active_checkpoints = tuple(checkpoint for checkpoint in self.checkpoints if checkpoint.findings)
        payload: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "overall_status": "hold" if active_checkpoints else "clear",
            "ready_for_enforcement_advisory": not active_checkpoints,
            "checkpoints": _checkpoint_json(self.checkpoints),
            "review_items": _review_items_json(active_checkpoints),
            "resource_versions": {
                "stopgate_rule_source_version": self.stopgate_payload.rule_source.version,
                "stopgate_rule_source_review_status": self.stopgate_payload.rule_source.review_status,
            },
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
            "non_execution_semantics": NON_EXECUTION_SEMANTICS,
        }
        return payload


def evaluate_legal_workflow_checkpoints(stopgate_payload: StopGatePayload) -> LegalWorkflowCheckpointResult:
    findings_by_reason = _findings_by_reason(stopgate_payload.findings)
    return LegalWorkflowCheckpointResult(
        stopgate_payload,
        tuple(
            LegalWorkflowCheckpoint(spec, _findings_for_spec(spec, findings_by_reason))
            for spec in CHECKPOINT_SPECS
        ),
    )


def _checkpoint_json(checkpoints: tuple[LegalWorkflowCheckpoint, ...]) -> list[JsonValue]:
    items: list[JsonValue] = []
    for checkpoint in checkpoints:
        items.append(checkpoint.to_json())
    return items


def _review_items_json(checkpoints: tuple[LegalWorkflowCheckpoint, ...]) -> list[JsonValue]:
    items: list[JsonValue] = []
    for checkpoint in checkpoints:
        items.append(_review_item(checkpoint))
    return items


CHECKPOINT_SPECS: Final = (
    CheckpointSpec("limitation", "limitation review", "satisfied", "limitation_review_hold", False),
    CheckpointSpec("enforcement_title", "enforcement title", "present", "title_acquisition_loop", False),
    CheckpointSpec("service_proof", "service proof", "present", "legal_precondition_review", False),
    CheckpointSpec("finality_proof", "finality proof", "present", "legal_precondition_review", False),
    CheckpointSpec("execution_clause", "execution clause", "present", "legal_precondition_review", False),
    CheckpointSpec("source_approval", "approved static legal source", "approved", "legal_source_review_hold", False),
    CheckpointSpec(
        "insolvency_or_protected_asset",
        "insolvency or protected asset review",
        "clear",
        "protected_asset_review_hold",
        True,
    ),
)

REASONS_BY_CHECKPOINT: Final = {
    "limitation": ("limitation_risk",),
    "enforcement_title": ("missing_enforcement_title",),
    "service_proof": ("missing_service_finality_execution_clause_proof",),
    "finality_proof": ("missing_service_finality_execution_clause_proof",),
    "execution_clause": ("missing_execution_clause", "missing_service_finality_execution_clause_proof"),
    "source_approval": (
        "domain_rule_source_unapproved",
        "domain_legal_source_unapproved",
        "route_legal_source_uncertain",
    ),
    "insolvency_or_protected_asset": (
        "discharge_proceeding_detected",
        "exempt_claim_targeted",
        "welfare_public_benefit_protected",
    ),
}


def _findings_by_reason(findings: tuple[StopGateFinding, ...]) -> dict[str, tuple[StopGateFinding, ...]]:
    grouped: dict[str, list[StopGateFinding]] = {}
    for finding in findings:
        grouped.setdefault(finding.rule.reason_code, []).append(finding)
    return {reason: tuple(items) for reason, items in grouped.items()}


def _findings_for_spec(
    spec: CheckpointSpec,
    findings_by_reason: dict[str, tuple[StopGateFinding, ...]],
) -> tuple[StopGateFinding, ...]:
    findings: list[StopGateFinding] = []
    for reason_code in REASONS_BY_CHECKPOINT[spec.checkpoint_id]:
        findings.extend(findings_by_reason.get(reason_code, ()))
    return tuple(findings)


def _status(spec: CheckpointSpec, findings: tuple[StopGateFinding, ...]) -> str:
    if not findings:
        return spec.clear_status
    if spec.blocked:
        return "blocked"
    if spec.checkpoint_id in {"enforcement_title", "service_proof", "finality_proof", "execution_clause"}:
        return "missing"
    return "review_required"


def _workflow_gate(spec: CheckpointSpec, findings: tuple[StopGateFinding, ...]) -> str:
    return spec.gate if findings else "none"


def _reason_codes(findings: tuple[StopGateFinding, ...]) -> list[JsonValue]:
    return _json_strings(sorted({finding.rule.reason_code for finding in findings}))


def _required_preconditions(findings: tuple[StopGateFinding, ...]) -> list[JsonValue]:
    return _json_strings(sorted({item for finding in findings for item in finding.rule.required_preconditions}))


def _missing_evidence(findings: tuple[StopGateFinding, ...]) -> list[JsonValue]:
    return _json_strings(sorted({item for finding in findings for item in finding.rule.missing_evidence}))


def _json_strings(values: list[str]) -> list[JsonValue]:
    items: list[JsonValue] = []
    for value in values:
        items.append(value)
    return items


def _source_refs(findings: tuple[StopGateFinding, ...]) -> list[JsonValue]:
    by_key: dict[str, JsonObject] = {}
    for finding in findings:
        for fact in finding.facts:
            by_key["{}:{}:{}".format(fact.source_ref, fact.document_id, fact.chunk_id)] = fact.to_json()
    items: list[JsonValue] = []
    for key in sorted(by_key):
        items.append(by_key[key])
    return items


def _review_item(checkpoint: LegalWorkflowCheckpoint) -> JsonObject:
    payload: JsonObject = {
        "code": checkpoint.spec.checkpoint_id,
        "category": "legal_workflow_checkpoint",
        "workflow_gate": checkpoint.spec.gate,
        "reason_codes": _reason_codes(checkpoint.findings),
        "required_preconditions": _required_preconditions(checkpoint.findings),
        "review_status": "human_review_required",
        "source_refs": _source_refs(checkpoint.findings),
    }
    return payload
