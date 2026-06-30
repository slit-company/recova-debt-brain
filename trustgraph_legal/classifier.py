from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Sequence, TypeAlias

from trustgraph_legal import __version__
from trustgraph_legal.registry import ONTOLOGY_VERSION, PROMPT_VERSION
from trustgraph_legal.pii import redact_text

# allow: SIZE_OK - Todo 5 keeps the classifier API, CLI, JSON contract, and deterministic rule table in one file.
JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
SignalSpec: TypeAlias = tuple[str, str, float]
RuleSpec: TypeAlias = tuple["FixtureBucket", tuple[SignalSpec, ...]]

SCHEMA_VERSION: Final = "trustgraph-legal-document-classifier/v1"
EXTRACTOR_VERSION: Final = f"trustgraph_legal.classifier@{__version__}"
UNKNOWN_CONFIDENCE_CEILING: Final = 0.49
MIN_CLASSIFICATION_SCORE: Final = 4.0


@unique
class FixtureBucket(StrEnum):
    ATTACHMENT_COLLECTION_ORDER = "attachment_collection_order"
    JUDGMENT_PAYMENT_ORDER = "judgment_payment_order"
    SERVICE_FINALITY_EXECUTION_CLAUSE = "service_finality_execution_clause"
    ASSIGNMENT_SUCCESSION = "assignment_succession"
    IDENTITY_EVIDENCE = "identity_evidence"
    INSOLVENCY_CREDIT_RECOVERY = "insolvency_credit_recovery"
    ASSET_EVIDENCE = "asset_evidence"
    OPERATIONAL_LEDGER = "operational_ledger"
    AMOUNT_INTEREST = "amount_interest"
    UNKNOWN_DOC_TYPE = "unknown_doc_type"


@unique
class CanonicalDocumentType(StrEnum):
    ATTACHMENT_COLLECTION_ORDER = "attachment-collection-order"
    PAYMENT_ORDER = "payment-order"
    SERVICE_FINALITY_PROOF = "service-finality-proof"
    ASSIGNMENT_SUCCESSION = "assignment-succession"
    IDENTITY_EVIDENCE = "identity-evidence"
    INSOLVENCY_CREDIT_RECOVERY = "insolvency-credit-recovery"
    ASSET_EVIDENCE = "asset-evidence"
    LEDGER_RECOVERY = "ledger-recovery"
    AMOUNT_INTEREST_CALCULATION = "amount-interest-calculation"
    UNKNOWN = "unknown"


@unique
class ReviewStatus(StrEnum):
    CLASSIFIED = "classified"
    NEEDS_REVIEW_UNKNOWN_DOC_TYPE = "needs_review_unknown_doc_type"


FIXTURE_BUCKET_TO_DOCUMENT_TYPE: Final[dict[FixtureBucket, CanonicalDocumentType]] = {
    FixtureBucket.ATTACHMENT_COLLECTION_ORDER: CanonicalDocumentType.ATTACHMENT_COLLECTION_ORDER,
    FixtureBucket.JUDGMENT_PAYMENT_ORDER: CanonicalDocumentType.PAYMENT_ORDER,
    FixtureBucket.SERVICE_FINALITY_EXECUTION_CLAUSE: CanonicalDocumentType.SERVICE_FINALITY_PROOF,
    FixtureBucket.ASSIGNMENT_SUCCESSION: CanonicalDocumentType.ASSIGNMENT_SUCCESSION,
    FixtureBucket.IDENTITY_EVIDENCE: CanonicalDocumentType.IDENTITY_EVIDENCE,
    FixtureBucket.INSOLVENCY_CREDIT_RECOVERY: CanonicalDocumentType.INSOLVENCY_CREDIT_RECOVERY,
    FixtureBucket.ASSET_EVIDENCE: CanonicalDocumentType.ASSET_EVIDENCE,
    FixtureBucket.OPERATIONAL_LEDGER: CanonicalDocumentType.LEDGER_RECOVERY,
    FixtureBucket.AMOUNT_INTEREST: CanonicalDocumentType.AMOUNT_INTEREST_CALCULATION,
    FixtureBucket.UNKNOWN_DOC_TYPE: CanonicalDocumentType.UNKNOWN,
}


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    source_ref: str
    start: int
    end: int
    excerpt: str
    signal: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "source_ref": self.source_ref,
            "start": self.start,
            "end": self.end,
            "excerpt": self.excerpt,
            "signal": self.signal,
        }


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    document_id: str
    document_type: CanonicalDocumentType
    fixture_document_type: FixtureBucket
    confidence: float
    review_status: ReviewStatus
    evidence_spans: tuple[EvidenceSpan, ...]
    reason_signals: tuple[str, ...]
    pii_counts: dict[str, int]

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "fixture_document_type": self.fixture_document_type.value,
            "confidence": self.confidence,
            "review_status": self.review_status.value,
            "reason_signals": list(self.reason_signals),
            "evidence_spans": [span.to_json() for span in self.evidence_spans],
            "source_refs": sorted({span.source_ref for span in self.evidence_spans}),
            "ocr_version": "MinerU@legal_ocr_20260630",
            "extractor_version": EXTRACTOR_VERSION,
            "ontology_version": ONTOLOGY_VERSION,
            "prompt_version": PROMPT_VERSION,
            "pii_profile": {
                "redacted": self.pii_counts,
                "raw_text_included": False,
            },
        }


@dataclass(frozen=True, slots=True)
class ClassificationPayload:
    records: tuple[ClassificationResult, ...]

    def to_json(self) -> dict[str, JsonValue]:
        unknown_count = sum(
            1
            for record in self.records
            if record.document_type is CanonicalDocumentType.UNKNOWN
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "summary": {
                "records": len(self.records),
                "classified": len(self.records) - unknown_count,
                "unknown_doc_type": unknown_count,
            },
            "records": [record.to_json() for record in self.records],
        }


@dataclass(frozen=True, slots=True)
class RuleMatch:
    fixture_bucket: FixtureBucket
    score: float
    evidence_spans: tuple[EvidenceSpan, ...]
    reason_signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManifestDocument:
    document_id: str
    source_fixture_path: str


class ClassifierInputError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()

    def __str__(self) -> str:
        return self.message


RULES: Final[tuple[RuleSpec, ...]] = (
    (
        FixtureBucket.ATTACHMENT_COLLECTION_ORDER,
        (
            ("채권압류 및 추심명령", "attachment_collection_order_marker", 4.0),
            ("Third-party debtor", "third_party_debtor_present", 2.0),
            ("The court orders attachment", "court_attachment_order_language", 2.0),
            ("may collect from the third-party debtor", "collection_authority_language", 1.5),
            ("Attachment target", "attachment_target_present", 1.0),
        ),
    ),
    (
        FixtureBucket.JUDGMENT_PAYMENT_ORDER,
        (
            ("지급명령 / 판결 정본", "judgment_payment_order_marker", 4.0),
            ("Delayed damages", "delayed_damages_present", 1.5),
            ("Decision summary", "decision_summary_present", 1.5),
            ("principal, accrued interest", "title_amount_language", 1.5),
            ("Objection and appeal status", "appeal_status_language", 1.0),
        ),
    ),
    (
        FixtureBucket.SERVICE_FINALITY_EXECUTION_CLAUSE,
        (
            ("송달증명 / 확정증명 / 집행문", "service_finality_execution_marker", 4.0),
            ("Service result", "service_result_present", 1.5),
            ("Finality result", "finality_result_present", 1.5),
            ("Execution clause", "execution_clause_present", 1.5),
            ("execution authority", "execution_authority_language", 1.0),
        ),
    ),
    (
        FixtureBucket.ASSIGNMENT_SUCCESSION,
        (
            ("채권양도 통지 / 승계집행문", "assignment_succession_marker", 4.0),
            ("Assignor", "assignor_present", 1.5),
            ("Assignee", "assignee_present", 1.5),
            ("Notice status", "notice_status_present", 1.5),
            ("Succession authority", "succession_authority_present", 1.5),
        ),
    ),
    (
        FixtureBucket.IDENTITY_EVIDENCE,
        (
            ("신원 확인 자료 / 법인등기 요약", "identity_evidence_marker", 4.0),
            ("Identity key evidence", "identity_key_evidence_present", 2.0),
            ("normalized name token", "name_token_present", 1.0),
            ("registration status", "registry_status_present", 1.0),
            ("representative role", "representative_role_present", 1.0),
        ),
    ),
    (
        FixtureBucket.INSOLVENCY_CREDIT_RECOVERY,
        (
            ("파산 / 면책 / 신용회복", "insolvency_credit_recovery_marker", 4.0),
            ("personal rehabilitation", "rehabilitation_present", 1.5),
            ("Procedure state", "procedure_state_present", 1.5),
            ("Discharge, rehabilitation", "discharge_rehabilitation_language", 1.5),
            ("Debt collection action must pause", "collection_pause_language", 1.0),
        ),
    ),
    (
        FixtureBucket.ASSET_EVIDENCE,
        (
            ("자산 증빙 / 압류대상 후보", "asset_evidence_marker", 4.0),
            ("Asset type", "asset_type_present", 1.5),
            ("Priority note", "priority_note_present", 1.5),
            ("Attachment suitability", "attachment_suitability_present", 1.5),
            ("Asset evidence suggests", "asset_evidence_language", 1.0),
        ),
    ),
    (
        FixtureBucket.OPERATIONAL_LEDGER,
        (
            ("채권보전 및 회수현황", "operational_ledger_marker", 4.0),
            ("Ledger rows", "ledger_rows_present", 2.0),
            ("partial recovery", "partial_recovery_present", 1.5),
            ("filing cost", "filing_cost_present", 1.0),
            ("operational facts", "operational_fact_language", 1.0),
        ),
    ),
    (
        FixtureBucket.AMOUNT_INTEREST,
        (
            ("원리금 계산서 / 지연손해금 산정", "amount_interest_marker", 4.0),
            ("Interest basis", "interest_basis_present", 1.5),
            ("Calculation start", "calculation_period_present", 1.5),
            ("Claimed total", "claimed_total_present", 1.5),
            ("principal, interest basis", "amount_interest_language", 1.0),
        ),
    ),
)


def classify_text(document_id: str, source_ref: str, text: str) -> ClassificationResult:
    redaction = redact_text(text)
    best_match = max((_match_rule(rule, source_ref, text) for rule in RULES), key=_rank)
    if best_match.score < MIN_CLASSIFICATION_SCORE:
        preview = _unknown_span(source_ref, redaction.text)
        return ClassificationResult(
            document_id=document_id,
            document_type=CanonicalDocumentType.UNKNOWN,
            fixture_document_type=FixtureBucket.UNKNOWN_DOC_TYPE,
            confidence=round(min(best_match.score / 10, UNKNOWN_CONFIDENCE_CEILING), 2),
            review_status=ReviewStatus.NEEDS_REVIEW_UNKNOWN_DOC_TYPE,
            evidence_spans=(preview,),
            reason_signals=("insufficient_document_type_signals",),
            pii_counts=redaction.counts,
        )
    return ClassificationResult(
        document_id=document_id,
        document_type=FIXTURE_BUCKET_TO_DOCUMENT_TYPE[best_match.fixture_bucket],
        fixture_document_type=best_match.fixture_bucket,
        confidence=_confidence(best_match.score),
        review_status=ReviewStatus.CLASSIFIED,
        evidence_spans=best_match.evidence_spans,
        reason_signals=best_match.reason_signals,
        pii_counts=redaction.counts,
    )


def classify_manifest(manifest_path: Path) -> ClassificationPayload:
    documents = _manifest_documents(manifest_path)
    records: list[ClassificationResult] = []
    for document in documents:
        source_path = _resolve_source_path(manifest_path, document.source_fixture_path)
        records.append(
            classify_text(
                document_id=document.document_id,
                source_ref=document.source_fixture_path,
                text=source_path.read_text(encoding="utf-8"),
            )
        )
    return ClassificationPayload(records=tuple(records))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m trustgraph_legal.classifier",
        description="Classify PII-safe legal OCR markdown fixtures.",
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    evidence_path = Path(args.evidence)
    payload = classify_manifest(manifest_path)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(payload.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(payload.records),
                "unknown_doc_type": sum(
                    1
                    for record in payload.records
                    if record.document_type is CanonicalDocumentType.UNKNOWN
                ),
                "evidence": str(evidence_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _rank(rule_match: RuleMatch) -> tuple[float, int]:
    return (rule_match.score, -list(FixtureBucket).index(rule_match.fixture_bucket))


def _match_rule(rule: RuleSpec, source_ref: str, text: str) -> RuleMatch:
    fixture_bucket, signal_specs = rule
    folded_text = text.casefold()
    spans: list[EvidenceSpan] = []
    signals: list[str] = []
    score = 0.0
    for needle, reason, weight in signal_specs:
        start = folded_text.find(needle.casefold())
        if start >= 0:
            end = start + len(needle)
            spans.append(
                EvidenceSpan(
                    source_ref=source_ref,
                    start=start,
                    end=end,
                    excerpt=_redacted_excerpt(text, start, end),
                    signal=reason,
                )
            )
            signals.append(reason)
            score += weight
    return RuleMatch(
        fixture_bucket=fixture_bucket,
        score=score,
        evidence_spans=tuple(spans),
        reason_signals=tuple(signals),
    )


def _confidence(score: float) -> float:
    return round(min(0.97, 0.62 + (score / 20)), 2)


def _unknown_span(source_ref: str, redacted_text: str) -> EvidenceSpan:
    end = min(len(redacted_text), 160)
    return EvidenceSpan(
        source_ref=source_ref,
        start=0,
        end=end,
        excerpt=redacted_text[:end],
        signal="low_signal_preview",
    )


def _redacted_excerpt(text: str, start: int, end: int) -> str:
    window_start = max(0, start - 80)
    window_end = min(len(text), end + 160)
    return redact_text(text[window_start:window_end].strip()).text


def _manifest_documents(manifest_path: Path) -> tuple[ManifestDocument, ...]:
    raw: JsonValue = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ClassifierInputError("manifest root must be a JSON object")
    documents = raw.get("documents")
    if not isinstance(documents, list):
        raise ClassifierInputError("manifest must contain documents list")
    parsed: list[ManifestDocument] = []
    for index, item in enumerate(documents):
        if not isinstance(item, dict):
            raise ClassifierInputError(f"manifest document {index} must be an object")
        document_id = item.get("document_id")
        source_fixture_path = item.get("source_fixture_path")
        if not isinstance(document_id, str) or not isinstance(source_fixture_path, str):
            raise ClassifierInputError(
                f"manifest document {index} is missing document_id or source_fixture_path"
            )
        parsed.append(
            ManifestDocument(
                document_id=document_id,
                source_fixture_path=source_fixture_path,
            )
        )
    return tuple(parsed)


def _resolve_source_path(manifest_path: Path, source_fixture_path: str) -> Path:
    raw_path = Path(source_fixture_path)
    if raw_path.is_absolute() and raw_path.exists():
        return raw_path
    search_roots = (Path.cwd(), *manifest_path.parents)
    for root in search_roots:
        candidate = root / raw_path
        if candidate.exists():
            return candidate
    raise ClassifierInputError(f"source fixture not found: {source_fixture_path}")


if __name__ == "__main__":
    raise SystemExit(main())
