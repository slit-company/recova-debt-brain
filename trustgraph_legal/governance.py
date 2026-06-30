from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from trustgraph_legal.governance_models import (
    CONTRACT_DOCUMENT_TYPE_GAPS,
    REQUIRED_APPROVAL_FIELDS,
    GovernancePayload,
    JsonValue,
    OntologyCandidate,
    PromotionAccepted,
    PromotionMetadata,
    PromotionRejected,
    PromotionResult,
)
from trustgraph_legal.governance_records import (
    contract_gap_candidates,
    governance_candidates,
    governance_review_items,
    reprocess_plans,
)
from trustgraph_legal.governance_sources import source_contexts


def build_governance_payload(
    manifest_path: Path,
    repo_root: Path,
    ontology_path: Path,
) -> GovernancePayload:
    contexts = source_contexts(manifest_path, repo_root)
    production_hash = _file_hash(ontology_path)
    candidates = governance_candidates(contexts)
    review_items = governance_review_items(contexts)
    plans = reprocess_plans(candidates, review_items)
    rejection = attempt_promotion(
        candidates[0] if candidates else contract_gap_candidates()[0],
        {},
        ontology_path,
    )
    return GovernancePayload(
        candidates=candidates,
        review_items=review_items,
        reprocess_plans=plans,
        promotion_results=(rejection,),
        production_ontology_hash=production_hash,
    )


def attempt_promotion(
    candidate: OntologyCandidate,
    metadata: dict[str, JsonValue],
    ontology_path: Path,
) -> PromotionResult:
    missing = tuple(
        field
        for field in REQUIRED_APPROVAL_FIELDS
        if _metadata_missing(metadata.get(field))
    )
    production_hash = _file_hash(ontology_path)
    if missing:
        return PromotionRejected(
            status="rejected",
            candidate_id=candidate.candidate_id,
            reason="missing_required_approval_metadata",
            missing_fields=missing,
            production_ontology_hash=production_hash,
        )
    parsed = _promotion_metadata(metadata)
    if parsed.regression_result != "pass":
        return PromotionRejected(
            status="rejected",
            candidate_id=candidate.candidate_id,
            reason="regression_result_must_pass",
            missing_fields=(),
            production_ontology_hash=production_hash,
        )
    return PromotionAccepted(
        status="approved-for-next-version",
        candidate_id=candidate.candidate_id,
        proposed_version="recova-debt-collection@v0-next",
        production_ontology_hash=production_hash,
        metadata=parsed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.governance")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ontology", required=True)
    parser.add_argument("--evidence", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_governance_payload(
        Path(args.manifest),
        Path(args.repo_root),
        Path(args.ontology),
    )
    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(payload.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(_stdout_summary(payload, evidence_path), ensure_ascii=False, sort_keys=True))
    return 0


def _stdout_summary(
    payload: GovernancePayload,
    evidence_path: Path,
) -> dict[str, JsonValue]:
    return {
        "candidates": len(payload.candidates),
        "review_items": len(payload.review_items),
        "reprocess_plans": len(payload.reprocess_plans),
        "candidate_ids": [candidate.candidate_id for candidate in payload.candidates],
        "review_item_ids": [item.review_item_id for item in payload.review_items],
        "source_refs": sorted(
            {
                source_ref
                for candidate in payload.candidates
                for source_ref in candidate.source_refs
            }
        ),
        "evidence": str(evidence_path),
    }


def _promotion_metadata(metadata: dict[str, JsonValue]) -> PromotionMetadata:
    changed_versions = metadata["changed_versions"]
    if not isinstance(changed_versions, list) or not all(
        isinstance(value, str) for value in changed_versions
    ):
        changed_versions = []
    return PromotionMetadata(
        approved_by=str(metadata["approved_by"]),
        approved_at=str(metadata["approved_at"]),
        approval_evidence_ref=str(metadata["approval_evidence_ref"]),
        regression_run_id=str(metadata["regression_run_id"]),
        fixture_set_id=str(metadata["fixture_set_id"]),
        changed_versions=tuple(changed_versions),
        regression_result=str(metadata["regression_result"]),
        unresolved_risk_summary=str(metadata["unresolved_risk_summary"]),
    )


def _metadata_missing(value: JsonValue) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value
    return False


def _file_hash(path: Path) -> str:
    return "sha256:{}".format(hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    raise SystemExit(main())
