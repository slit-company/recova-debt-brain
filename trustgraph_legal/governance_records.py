from __future__ import annotations

import hashlib

from trustgraph_legal.classifier import CanonicalDocumentType, ClassificationResult
from trustgraph_legal.governance_models import (
    CONTRACT_DOCUMENT_TYPE_GAPS,
    EXTRACTOR_VERSION,
    ONTOLOGY_VERSION,
    PROMPT_VERSION,
    JsonValue,
    OntologyCandidate,
    ReprocessPlan,
    ReviewItem,
    SourceContext,
)


def governance_candidates(
    contexts: tuple[SourceContext, ...],
) -> tuple[OntologyCandidate, ...]:
    return _document_candidates(contexts) + contract_gap_candidates()


def governance_review_items(contexts: tuple[SourceContext, ...]) -> tuple[ReviewItem, ...]:
    return _document_review_items(contexts) + _contract_gap_review_items()


def contract_gap_candidates() -> tuple[OntologyCandidate, ...]:
    return tuple(
        OntologyCandidate(
            candidate_id=_id("candidate", doc_type, "contract-gap"),
            candidate_type="document_type",
            proposed_id=doc_type,
            proposed_label=doc_type.replace("-", " ").title(),
            reason="domain_contract_type_not_production_supported_in_v0_classifier",
            status="v0-excluded-review-required",
            source_refs=("docs/product/debt-collection-ontology/domain-contract.md",),
            provenance={
                "source_ref": "docs/product/debt-collection-ontology/domain-contract.md",
                "extractor_version": EXTRACTOR_VERSION,
                "ontology_version": ONTOLOGY_VERSION,
            },
            risk_flags=(
                "ontology-candidate",
                "classifier-coverage-gap",
                "no-auto-promotion",
            ),
        )
        for doc_type in CONTRACT_DOCUMENT_TYPE_GAPS
    )


def reprocess_plans(
    candidates: tuple[OntologyCandidate, ...],
    review_items: tuple[ReviewItem, ...],
) -> tuple[ReprocessPlan, ...]:
    plans: list[ReprocessPlan] = []
    for candidate in candidates:
        plans.append(
            ReprocessPlan(
                reprocess_plan_id=_id("reprocess", candidate.candidate_id),
                trigger="ontology-candidate",
                document_ids=_matching_documents(candidate, review_items),
                changed_versions={
                    "ontology_version": "proposed:{}".format(candidate.proposed_id),
                    "extractor_version": EXTRACTOR_VERSION,
                    "prompt_version": PROMPT_VERSION,
                },
                required_evidence=(
                    "regression_run_id",
                    "fixture_set_id",
                    "approval_evidence_ref",
                ),
                source_refs=candidate.source_refs,
                status="planned",
                reason=candidate.reason,
            )
        )
    return tuple(plans)


def _document_candidates(
    contexts: tuple[SourceContext, ...],
) -> tuple[OntologyCandidate, ...]:
    candidates: list[OntologyCandidate] = []
    for context in contexts:
        if context.classifier.document_type is CanonicalDocumentType.UNKNOWN:
            candidates.append(_unknown_document_type_candidate(context))
        if context.fields.review_status == "needs_review":
            candidates.append(_low_confidence_field_candidate(context))
    return tuple(candidates)


def _unknown_document_type_candidate(context: SourceContext) -> OntologyCandidate:
    return OntologyCandidate(
        candidate_id=_id("candidate", context.document.document_id, "unknown-type"),
        candidate_type="document_type",
        proposed_id="unknown-document-type-candidate",
        proposed_label="Unknown document type candidate",
        reason="classifier_returned_unknown",
        status="draft-review-required",
        source_refs=_classifier_source_refs(context.classifier),
        provenance=_document_provenance(context),
        risk_flags=("unknown-document-type", "no-auto-promotion"),
    )


def _low_confidence_field_candidate(context: SourceContext) -> OntologyCandidate:
    return OntologyCandidate(
        candidate_id=_id("candidate", context.document.document_id, "low-confidence"),
        candidate_type="property_or_extractor_gap",
        proposed_id="low-confidence-field-review",
        proposed_label="Low confidence extracted field candidate",
        reason=context.fields.review_reason or "low_confidence_extraction",
        status="draft-review-required",
        source_refs=("fixture:{}".format(context.document.source_fixture_path),),
        provenance=_document_provenance(context),
        risk_flags=("low-confidence-extraction", "source-provenance-required"),
    )


def _document_review_items(contexts: tuple[SourceContext, ...]) -> tuple[ReviewItem, ...]:
    items: list[ReviewItem] = []
    for context in contexts:
        if context.classifier.document_type is CanonicalDocumentType.UNKNOWN:
            items.append(
                _review_item(
                    "unknown-document-type",
                    context.document.document_id,
                    "unknown",
                    None,
                    "classifier_returned_unknown",
                    ("unknown-document-type",),
                    _classifier_source_refs(context.classifier),
                )
            )
        if context.fields.review_status == "needs_review":
            items.append(
                _review_item(
                    "low-confidence-extraction",
                    context.document.document_id,
                    context.fields.document_type,
                    None,
                    context.fields.review_reason or "low_confidence_extraction",
                    ("low-confidence-extraction",),
                    ("fixture:{}".format(context.document.source_fixture_path),),
                )
            )
    return tuple(items)


def _contract_gap_review_items() -> tuple[ReviewItem, ...]:
    return tuple(
        _review_item(
            "ontology-candidate",
            None,
            doc_type,
            "not-supported-in-v0-classifier",
            "domain_contract_type_requires_candidate_or_explicit_v0_exclusion",
            ("classifier-coverage-gap", "version-promotion-required"),
            ("docs/product/debt-collection-ontology/domain-contract.md",),
        )
        for doc_type in CONTRACT_DOCUMENT_TYPE_GAPS
    )


def _review_item(
    queue_id: str,
    document_id: str | None,
    candidate_value: str,
    current_value: str | None,
    reason: str,
    risk_flags: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> ReviewItem:
    return ReviewItem(
        review_item_id=_id("review", queue_id, document_id or candidate_value, reason),
        queue_id=queue_id,
        document_id=document_id,
        candidate_value=candidate_value,
        current_value=current_value,
        reason=reason,
        risk_flags=risk_flags,
        source_refs=source_refs,
        redaction_status="redacted-output",
        status="open",
    )


def _matching_documents(
    candidate: OntologyCandidate,
    review_items: tuple[ReviewItem, ...],
) -> tuple[str, ...]:
    return tuple(
        item.document_id
        for item in review_items
        if item.document_id is not None
        and candidate.candidate_id.startswith(_id("candidate", item.document_id)[:28])
    )


def _document_provenance(context: SourceContext) -> dict[str, JsonValue]:
    return {
        "document_id": context.document.document_id,
        "source_ref": "fixture:{}".format(context.document.source_fixture_path),
        "source_hash": context.document.source_hash,
        "classifier_confidence": context.classifier.confidence,
        "field_confidence": context.fields.confidence,
        "extractor_version": EXTRACTOR_VERSION,
        "ontology_version": ONTOLOGY_VERSION,
    }


def _classifier_source_refs(result: ClassificationResult) -> tuple[str, ...]:
    return tuple(sorted({span.source_ref for span in result.evidence_spans}))


def _id(prefix: str, *parts: str) -> str:
    return "{}:{}".format(
        prefix,
        hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20],
    )
