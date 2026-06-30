from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional, Union

from trustgraph_legal import __version__
from trustgraph_legal.classifier import ClassificationResult
from trustgraph_legal.fields import FieldExtractionResult

JsonScalar = Optional[Union[str, int, float, bool]]
JsonValue = Union[JsonScalar, list["JsonValue"], dict[str, "JsonValue"]]

SCHEMA_VERSION: Final = "trustgraph-legal-ontology-governance/v1"
EXTRACTOR_VERSION: Final = "trustgraph_legal.governance@{}".format(__version__)
ONTOLOGY_ID: Final = "recova-debt-collection"
ONTOLOGY_VERSION: Final = "recova-debt-collection@v0"
PROMPT_VERSION: Final = "legal-ontology-extraction@v0"
REQUIRED_APPROVAL_FIELDS: Final = (
    "approved_by",
    "approved_at",
    "approval_evidence_ref",
    "regression_run_id",
    "fixture_set_id",
    "changed_versions",
    "regression_result",
    "unresolved_risk_summary",
)
CONTRACT_DOCUMENT_TYPE_GAPS: Final = (
    "attachment-collection-application",
    "judgment-or-decision",
    "attachment-target-priority",
    "legal-rule-source",
)


@dataclass(frozen=True)
class ManifestDocument:
    document_id: str
    document_type: str
    source_fixture_path: str
    source_hash: str


@dataclass(frozen=True)
class SourceContext:
    document: ManifestDocument
    classifier: ClassificationResult
    fields: FieldExtractionResult


@dataclass(frozen=True)
class OntologyCandidate:
    candidate_id: str
    candidate_type: str
    proposed_id: str
    proposed_label: str
    reason: str
    status: str
    source_refs: tuple[str, ...]
    provenance: dict[str, JsonValue]
    risk_flags: tuple[str, ...]

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "proposed_id": self.proposed_id,
            "proposed_label": self.proposed_label,
            "reason": self.reason,
            "status": self.status,
            "source_refs": list(self.source_refs),
            "provenance": self.provenance,
            "risk_flags": list(self.risk_flags),
        }


@dataclass(frozen=True)
class ReviewItem:
    review_item_id: str
    queue_id: str
    document_id: str | None
    candidate_value: str
    current_value: str | None
    reason: str
    risk_flags: tuple[str, ...]
    source_refs: tuple[str, ...]
    redaction_status: str
    status: str
    approval_evidence_ref: str | None = None

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "review_item_id": self.review_item_id,
            "queue_id": self.queue_id,
            "case_packet_id": None,
            "document_id": self.document_id,
            "fact_id": None,
            "candidate_value": self.candidate_value,
            "current_value": self.current_value,
            "reason": self.reason,
            "risk_flags": list(self.risk_flags),
            "source_refs": list(self.source_refs),
            "redaction_status": self.redaction_status,
            "status": self.status,
            "created_at": "2026-06-30T00:00:00Z",
            "updated_at": "2026-06-30T00:00:00Z",
            "assigned_to": None,
            "resolution": None,
            "resolution_reason": None,
            "approved_by": None,
            "approval_evidence_ref": self.approval_evidence_ref,
        }


@dataclass(frozen=True)
class ReprocessPlan:
    reprocess_plan_id: str
    trigger: str
    document_ids: tuple[str, ...]
    changed_versions: dict[str, JsonValue]
    required_evidence: tuple[str, ...]
    source_refs: tuple[str, ...]
    status: str
    reason: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "reprocess_plan_id": self.reprocess_plan_id,
            "queue_id": "case-reprocess",
            "trigger": self.trigger,
            "document_ids": list(self.document_ids),
            "changed_versions": self.changed_versions,
            "required_evidence": list(self.required_evidence),
            "source_refs": list(self.source_refs),
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PromotionMetadata:
    approved_by: str
    approved_at: str
    approval_evidence_ref: str
    regression_run_id: str
    fixture_set_id: str
    changed_versions: tuple[str, ...]
    regression_result: str
    unresolved_risk_summary: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "approval_evidence_ref": self.approval_evidence_ref,
            "regression_run_id": self.regression_run_id,
            "fixture_set_id": self.fixture_set_id,
            "changed_versions": list(self.changed_versions),
            "regression_result": self.regression_result,
            "unresolved_risk_summary": self.unresolved_risk_summary,
        }


@dataclass(frozen=True)
class PromotionAccepted:
    status: str
    candidate_id: str
    proposed_version: str
    production_ontology_hash: str
    metadata: PromotionMetadata

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "candidate_id": self.candidate_id,
            "proposed_version": self.proposed_version,
            "production_ontology_hash": self.production_ontology_hash,
            "metadata": self.metadata.to_json(),
            "production_ontology_modified": False,
        }


@dataclass(frozen=True)
class PromotionRejected:
    status: str
    candidate_id: str
    reason: str
    missing_fields: tuple[str, ...]
    production_ontology_hash: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "candidate_id": self.candidate_id,
            "reason": self.reason,
            "missing_fields": list(self.missing_fields),
            "production_ontology_hash": self.production_ontology_hash,
            "production_ontology_modified": False,
        }


PromotionResult = PromotionAccepted | PromotionRejected


@dataclass(frozen=True)
class GovernancePayload:
    candidates: tuple[OntologyCandidate, ...]
    review_items: tuple[ReviewItem, ...]
    reprocess_plans: tuple[ReprocessPlan, ...]
    promotion_results: tuple[PromotionResult, ...]
    production_ontology_hash: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "schema_version": SCHEMA_VERSION,
            "ontology_id": ONTOLOGY_ID,
            "ontology_version": ONTOLOGY_VERSION,
            "prompt_version": PROMPT_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "summary": {
                "candidates": len(self.candidates),
                "review_items": len(self.review_items),
                "reprocess_plans": len(self.reprocess_plans),
                "promotion_results": len(self.promotion_results),
            },
            "production_ontology_hash": self.production_ontology_hash,
            "production_ontology_modified": False,
            "pii_profile": {
                "raw_text_included": False,
                "source_text_included": False,
            },
            "candidates": [candidate.to_json() for candidate in self.candidates],
            "review_items": [item.to_json() for item in self.review_items],
            "reprocess_plans": [plan.to_json() for plan in self.reprocess_plans],
            "promotion_results": [result.to_json() for result in self.promotion_results],
        }
